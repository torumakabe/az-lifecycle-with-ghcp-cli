---
name: azd-hooks
description: "azd フック（pre/postprovision）の作成・編集と azure.yaml のフック設定。PostgreSQL Entra ID ユーザー作成の運用パターンを含む。WHEN: hooks/, preprovision, postprovision, azure.yaml, azd provision, azd up, azd deploy, pgaadauth, PostgreSQL user creation, hook script"
---

# azd Hooks

azd フックの実装ルールとテンプレートを扱う。Bicep パラメータ設計・ネットワーク構成は [azd-infra-rules](../azd-infra-rules/SKILL.md) を先に参照すること。フックが参照する環境変数は `main.bicep` の `output` から受け取る。

## フックスクリプトの規約

- hooks は Python + `uv run` 前提。`.sh`/`.ps1` を新設しない
- 単一ファイルスクリプトには **PEP 723 インラインメタデータ**（`# /// script`）で依存を宣言する
- `azure.yaml` は `posix` / `windows` 両セクションを指定し、`run` の値を同一の `uv run` コマンドにする

## デプロイ時の注意（azd up / provision）

- **`--no-prompt` は使わない** — preprovision フックがパラメータを自動設定する設計のため、`--no-prompt` ではパラメータ検証がフック実行前に走り失敗する（[azure-dev#3920](https://github.com/Azure/azure-dev/issues/3920)）
- **認証情報をユーザーに質問しない** — `pgAdminObjectId` / `pgAdminLoginName` は preprovision フックが `az login` 済みの認証情報から自動取得する
- デプロイ前に `azd env get-values` で未設定パラメータがないか確認する（`pgAdminObjectId` / `pgAdminLoginName` は初回実行前に未設定でも想定内 — preprovision が補完する）

## postprovision フックの不変条件

`hooks/postprovision.py` を新規作成・修正する場合は [references/postprovision-template.md](references/postprovision-template.md) を先に読むこと。以下の条件を必ず守る:

1. **`pgaadauth_create_principal` は `postgres` DB で実行** — ユーザー DB には存在しない（[references/postgresql-entra-id-provisioning.md](references/postgresql-entra-id-provisioning.md)）
2. **`az postgres flexible-server execute` を優先** — `psql` 未インストール環境でも動作させる。失敗時のみ `psql` フォールバック
3. **`resolve_command()` でコマンドパスを解決** — Windows で PATH が通っていない環境への対応
4. **IPv4 を強制** — PostgreSQL ファイアウォールは IPv4 のみ。`api.ipify.org` で取得
5. **`try/finally` でファイアウォール規則を確実に削除**
6. **SQL 識別子をエスケープ** — `replace('"', '""')` で `"` に対応
7. **private-only 構成では失敗時にスキップ** — まず CLI 実行を試み、失敗した場合のみ警告して正常終了（`SystemExit` で異常終了させない）
8. **CLI パス (`execute_sql_via_cli`) でも一時ファイアウォール規則を追加する** — `az postgres flexible-server execute` は実行ホストの IP を自動許可しない。`enableDatabasePublicAccess=true` でも CLI 実行元から PostgreSQL へ到達できず接続タイムアウトする。psql フォールバックと同様、try/finally で `firewall-rule create --start-ip-address` / `firewall-rule delete` を囲むこと

## preprovision フックの不変条件

`hooks/preprovision.py` を扱う場合は [references/preprovision-template.md](references/preprovision-template.md) を先に読むこと。

- `azure-identity` の `AzureCliCredential` で Microsoft Graph `/me` を呼び出し、`pgAdminObjectId` / `pgAdminLoginName` を自動取得して `azd env set` で永続化する
- `subprocess` で `az` を直接呼ばず Python SDK を使う（Windows での `az.cmd` パス問題の回避）

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
