# postprovision フックテンプレート

PostgreSQL の Entra ID ユーザーを作成する postprovision フック。
ルールと不変条件は [SKILL.md](../SKILL.md) を参照。

## Python (hooks/postprovision.py)

```python
# /// script
# requires-python = ">=3.9"
# ///
"""postprovision: PostgreSQL の Entra ID principal を作成する"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request


def run(cmd: list[str], *, check: bool = True, capture: bool = False, input_text: str | None = None) -> str:
    result = subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
        input=input_text,
    )
    return result.stdout.strip() if capture else ""


def get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Required environment variable is missing: {name}")
    return value


def resolve_command(name: str) -> str:
    resolved = shutil.which(name)
    if resolved:
        return resolved

    windows_fallbacks = {
        "az": [
            r"C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd",
        ],
        "psql": [
            r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
        ],
    }

    for candidate in windows_fallbacks.get(name, []):
        if os.path.exists(candidate):
            return candidate

    raise SystemExit(f"Required command is not available: {name}")


def get_current_ipv4() -> str:
    with urllib.request.urlopen("https://api.ipify.org", timeout=10) as response:
        return response.read().decode().strip()


def get_access_token() -> str:
    az = resolve_command("az")
    return run(
        [az, "account", "get-access-token",
         "--resource-type", "oss-rdbms", "--query", "accessToken", "-o", "tsv"],
        capture=True,
    )


def build_sql(managed_identity_name: str, postgres_database_name: str) -> str:
    escaped_identity_name_literal = managed_identity_name.replace("'", "''")
    escaped_identity_name_identifier = managed_identity_name.replace('"', '""')
    escaped_database_name = postgres_database_name.replace('"', '""')

    return f"""DO $$
BEGIN
  PERFORM pgaadauth_create_principal('{escaped_identity_name_literal}', false, false);
EXCEPTION WHEN duplicate_object THEN
  RAISE NOTICE 'Principal already exists, skipping.';
END
$$;
GRANT ALL PRIVILEGES ON DATABASE "{escaped_database_name}" TO "{escaped_identity_name_identifier}";
"""


def execute_sql_via_cli(
    resource_group: str,
    server_name: str,
    pg_admin_login_name: str,
    sql: str,
) -> None:
    az = resolve_command("az")
    token = get_access_token()
    # `az postgres flexible-server execute` は実行ホスト IP を自動許可しない。
    # enableDatabasePublicAccess=true でも一時ファイアウォール規則が必要。
    current_ip = get_current_ipv4()
    firewall_rule_name = f"temp-postprovision-cli-{int(time.time())}"

    run([
        az, "postgres", "flexible-server", "firewall-rule", "create",
        "--resource-group", resource_group,
        "--name", server_name,
        "--rule-name", firewall_rule_name,
        "--start-ip-address", current_ip, "--end-ip-address", current_ip,
    ])

    with tempfile.NamedTemporaryFile("w", suffix=".sql", encoding="utf-8", delete=False) as sql_file:
        sql_file.write(sql)
        sql_file_path = sql_file.name

    try:
        run(
            [az, "postgres", "flexible-server", "execute",
             "--name", server_name,
             "--admin-user", pg_admin_login_name,
             "--admin-password", token,
             "--database-name", "postgres",
             "--file-path", sql_file_path],
        )
    finally:
        try:
            os.unlink(sql_file_path)
        except FileNotFoundError:
            pass
        run([
            az, "postgres", "flexible-server", "firewall-rule", "delete",
            "--resource-group", resource_group,
            "--name", server_name,
            "--rule-name", firewall_rule_name, "--yes",
        ], check=False)


def execute_sql_via_psql(
    postgres_fqdn: str,
    resource_group: str,
    server_name: str,
    pg_admin_login_name: str,
    sql: str,
) -> None:
    az = resolve_command("az")
    psql = resolve_command("psql")
    current_ip = get_current_ipv4()
    firewall_rule_name = f"temp-postprovision-{int(time.time())}"

    run([
        az, "postgres", "flexible-server", "firewall-rule", "create",
        "--resource-group", resource_group,
        "--name", server_name,
        "--rule-name", firewall_rule_name,
        "--start-ip-address", current_ip, "--end-ip-address", current_ip,
    ])

    try:
        os.environ["PGPASSWORD"] = get_access_token()
        run(
            [psql, f"host={postgres_fqdn} dbname=postgres user={pg_admin_login_name} sslmode=require"],
            input_text=sql,
        )
    finally:
        run([
            az, "postgres", "flexible-server", "firewall-rule", "delete",
            "--resource-group", resource_group,
            "--name", server_name,
            "--rule-name", firewall_rule_name, "--yes",
        ], check=False)


def main() -> None:
    private_networking_enabled = os.environ.get("ENABLE_PRIVATE_NETWORKING", "").lower() == "true"

    postgres_fqdn = get_required_env("POSTGRES_FQDN")
    resource_group = get_required_env("AZURE_RESOURCE_GROUP")
    managed_identity_name = get_required_env("MANAGED_IDENTITY_NAME")
    pg_admin_login_name = get_required_env("PG_ADMIN_LOGIN_NAME")
    postgres_database_name = get_required_env("POSTGRES_DATABASE_NAME")

    server_name = postgres_fqdn.split(".", 1)[0]
    sql = build_sql(managed_identity_name, postgres_database_name)

    try:
        execute_sql_via_cli(resource_group, server_name, pg_admin_login_name, sql)
    except subprocess.CalledProcessError:
        if private_networking_enabled:
            print(
                "==> Private networking is enabled and CLI SQL execution failed. "
                "Skipping PostgreSQL Entra principal creation. "
                "Create the principal from within the VNet separately."
            )
            return
        execute_sql_via_psql(postgres_fqdn, resource_group, server_name, pg_admin_login_name, sql)

    print(f"==> PostgreSQL principal ensured for managed identity: {managed_identity_name}")


if __name__ == "__main__":
    sys.exit(main())
```
