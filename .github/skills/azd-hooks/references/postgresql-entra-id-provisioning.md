# PostgreSQL Entra ID ユーザーのプロビジョニング

PostgreSQL Flexible Server で Entra ID ユーザーを作成する際の運用パターン。

## pgaadauth_create_principal の実行先

`pgaadauth_create_principal` 関数は **`postgres` データベースにのみ存在する**。`app` 等のユーザーデータベースには存在しないため、必ず `dbname=postgres` に接続して実行すること。

```bash
# ✅ 正しい: postgres DB に接続
psql "host=${POSTGRES_FQDN} dbname=postgres user=${PG_ADMIN_LOGIN_NAME} sslmode=require"

# ❌ 誤り: app DB に接続（pgaadauth_create_principal が見つからない）
psql "host=${POSTGRES_FQDN} dbname=app user=${PG_ADMIN_LOGIN_NAME} sslmode=require"
```

## User-Assigned MI の名前

`CREATE USER` および `pgaadauth_create_principal` に渡す名前は **Managed Identity のリソース名**（`id-*`）を使う。App Service 名（`app-*`）ではない。名前が不一致だと認証が失敗する。

Bicep から MI 名を出力し、フックで環境変数として参照する:

```bicep
// resources.bicep
output managedIdentityName string = managedIdentity.name

// main.bicep
output MANAGED_IDENTITY_NAME string = resources.outputs.managedIdentityName
```

## VNet + Private Endpoint 構成時の到達性

ネットワーク構成は Bicep の `enablePrivateNetworking` パラメータ（bool）で制御する:

| `enablePrivateNetworking` | `publicNetworkAccess` | VNet/PE | postprovision フックの DB ユーザー作成 |
|---|---|---|---|
| `false` | `Enabled` | なし | 一時ファイアウォール規則で接続し、実行する |
| `true` | `Disabled` | 作成される | VNet 外から到達できないため、スキップする（警告メッセージを表示） |

`enablePrivateNetworking: true` の場合、VNet 外の `psql` は PostgreSQL に到達できない。postprovision フックは DB ユーザー作成をスキップし、警告メッセージを出力する。ユーザー未作成のままアプリをデプロイすると DB 接続エラーになる。

> **⚠️ パラメータ設計の注意**: `enableVnetIntegration` と `postgresPublicAccess` を独立したパラメータにしないこと。`enablePrivateNetworking` 1つで制御し、`publicNetworkAccess` は Bicep 内で導出する。

### DB ユーザー作成の代替手段（`enablePrivateNetworking: true` 時）

- **Azure Deployment Script**: ARM/Bicep デプロイの一部として VNet 内でスクリプトを実行できる
- **VNet 内 CI/CD ランナー**: GitHub Actions self-hosted runner 等を VNet 内に配置
- **Bastion / Jump Box**: 手動またはスクリプト経由で VNet 内から実行

## pgaadauth 拡張について

Entra ID 管理者設定後にプラットフォームが自動で `pgaadauth` を読み込む。`azure.extensions` や `shared_preload_libraries` にユーザーが追加することはできない（許可リストにない）。
