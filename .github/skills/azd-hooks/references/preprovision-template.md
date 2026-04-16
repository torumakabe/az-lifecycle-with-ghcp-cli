# preprovision フックテンプレート

`pgAdminObjectId` / `pgAdminLoginName` が未設定の場合、`azure-identity` の `AzureCliCredential` で Microsoft Graph `/me` を呼び出し、ログインユーザーの情報を自動取得して `azd env set` で永続化する。

`subprocess` で `az` CLI を直接呼ばず Python SDK を使うことで、Windows での `az.cmd` パス問題を回避する。

## Python (hooks/preprovision.py)

```python
# /// script
# requires-python = ">=3.9"
# dependencies = ["azure-identity>=1.16"]
# ///
"""preprovision: pgAdminObjectId / pgAdminLoginName を自動検出・設定する

未設定の場合、Azure CLI の認証情報を使って Microsoft Graph /me から
ログインユーザーの objectId と UPN を取得し、azd env set で永続化する。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request


def resolve_command(name: str) -> str:
    """コマンドのフルパスを返す。見つからなければ終了する。"""
    resolved = shutil.which(name)
    if resolved:
        return resolved
    raise SystemExit(f"Required command is not available: {name}")


def get_signed_in_user() -> dict[str, str]:
    """AzureCliCredential で Microsoft Graph /me を呼び出し、id と userPrincipalName を返す。"""
    from azure.identity import AzureCliCredential

    credential = AzureCliCredential()
    token = credential.get_token("https://graph.microsoft.com/.default")

    req = urllib.request.Request(
        "https://graph.microsoft.com/v1.0/me?$select=id,userPrincipalName",
        headers={"Authorization": f"Bearer {token.token}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    return {"id": data["id"], "userPrincipalName": data["userPrincipalName"]}


def azd_env_set(name: str, value: str) -> None:
    """azd env set を呼んで環境変数を永続化する。"""
    azd = resolve_command("azd")
    subprocess.run([azd, "env", "set", name, value], check=True)


def main() -> None:
    object_id = os.environ.get("pgAdminObjectId")
    login_name = os.environ.get("pgAdminLoginName")

    if object_id and login_name:
        print("==> PostgreSQL admin values are already set.")
        return

    print("==> PostgreSQL admin values not set. Auto-detecting from signed-in user...")

    try:
        me = get_signed_in_user()
    except Exception as exc:
        print(
            f"ERROR: Failed to auto-detect Entra ID user info: {exc}\n\n"
            "Ensure you are logged in with 'az login' and try again.\n\n"
            "Alternatively, set the values manually:\n"
            "  azd env set pgAdminObjectId <your-entra-object-id>\n"
            "  azd env set pgAdminLoginName <your-entra-upn>\n",
            file=sys.stderr,
        )
        sys.exit(1)

    object_id = me["id"]
    login_name = me["userPrincipalName"]

    azd_env_set("pgAdminObjectId", object_id)
    azd_env_set("pgAdminLoginName", login_name)

    print(f"==> Auto-detected and set: pgAdminObjectId={object_id}, pgAdminLoginName={login_name}")


if __name__ == "__main__":
    main()
```

## azure.yaml のフック設定

```yaml
hooks:
  preprovision:
    posix:
      shell: sh
      run: uv run hooks/preprovision.py
    windows:
      shell: pwsh
      run: uv run hooks/preprovision.py
  postprovision:
    posix:
      shell: sh
      run: uv run hooks/postprovision.py
    windows:
      shell: pwsh
      run: uv run hooks/postprovision.py
```
