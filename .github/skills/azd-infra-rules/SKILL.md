---
name: azd-infra-rules
description: "azd 前提の IaC ルール。Bicep、azure.yaml、hooks をまたぐ repo 固有ルールを扱う。WHEN: infra/, .bicep, azure.yaml, hooks/, preprovision, postprovision, targetScope, main.parameters.json, enableDatabasePublicAccess"
---

# azd Infra Rules

## このスキルの役割

このファイルには**リポジトリ固有の設計判断だけ**を書く。汎用的な Bicep / Azure の推奨事項は外部ソースに委譲する。

1. **Azure 系プラグイン** — Azure 全般の構成判断、リソース選定、サービス固有の定番構成
2. **AVM の WAF-aligned 例** — リソースごとの実装パターン
   - GitHub MCP Server で `repo:Azure/bicep-registry-modules WAF-aligned {resource type}` を検索
3. **Microsoft Learn** — Bicep の一般論とリソース スキーマ
   - `microsoft_docs_fetch(url="https://learn.microsoft.com/azure/azure-resource-manager/bicep/best-practices")`
   - `microsoft_docs_search(query="{resource type} bicep template")`

## このリポジトリ固有のルール

詳細な背景は [references/azd-infra-rules.md](references/azd-infra-rules.md) を参照。

- **azd 前提のテンプレートにする** — `targetScope = 'subscription'` とし、リソース グループ作成をテンプレートに含める
- **azd 標準パラメータを省略しない** — `environmentName` と `location` を必須で受け取る
- **`environmentName` は用途を示す短い名前にする** — `poc`、`dev`、`prod` など。リソース名が `{prefix}-${workloadName}-${environmentName}`（例: `app-myproj-poc`）で構成されるため、ディレクトリ名のデフォルトではなく `azd init -e poc` のように明示的に指定する
- **グローバル一意が必要なリソースには `resourceToken` サフィックスを付ける** — `uniqueString(subscription().subscriptionId, environmentName, location)` の先頭5文字を App Service・PostgreSQL などホスト名がグローバル一意なリソースに付与する。RG・Log Analytics など一意性が不要なリソースには付けない
- **パラメータ ファイルは `main.parameters.json` を優先** — この repo では azd テンプレートとの一貫性と `@minLength` との相性を優先する
- **Bicep outputs を hooks / `azure.yaml` の契約として扱う** — フックが参照する値は `main.bicep` の `output` に明示する
- **VNet・App Service VNet 統合・PostgreSQL PE は常に作成する** — PoC でも本番でもネットワーク構成は同じ。App Service → PostgreSQL は常に PE 経由のプライベート接続とする。PoC で性能基礎値を測るには本番と同じ通信経路が必要なため
- **PostgreSQL の DB パブリックアクセスは `enableDatabasePublicAccess` の単一 bool で制御** — `true`（PoC）: PE に加えてパブリックアクセスも有効にし、開発者が psql で直接接続できるようにする。`false`（本番）: パブリックアクセス無効、PE のみ。`enableVnetIntegration` と `postgresPublicAccess` を独立パラメータにしない。**デフォルト値は `false`（Secure-by-default）** — PoC では `azd env set enableDatabasePublicAccess true` で明示的に有効化する
- **Azure Policy が管理するリソース構成と競合させない** — サブスクリプションやマネジメントグループの Azure Policy がリソース構成（診断設定、タグ、ネットワーク制限など）を強制している場合、Bicep の定義を Policy に合わせる。Policy と矛盾するテンプレートはデプロイ失敗または意図しないドリフトを引き起こす
- **Bicep でリソースを追加したら診断設定を必ず作成する** — 対象リソースごとに `Microsoft.Insights/diagnosticSettings` を作成し、ログとメトリクス（`AllMetrics`）を Log Analytics ワークスペースに送信する。ログカテゴリは対象リソースの Microsoft Learn ドキュメントで確認すること
- **ログの取り込みコスト削減が求められる場合は Basic テーブルプランと診断設定のカテゴリ絞り込みを検討する** — 詳細は [references/azd-infra-rules.md](references/azd-infra-rules.md) の「ログ取り込みコストの最適化」セクションを参照
- **App Service は Premium V3（P0v3 以上）を原則とする** — リモートビルドのタイムアウト回避と本番同等の性能基礎値取得のため。Basic / Standard は使わない
- **DB パブリックアクセス無効の構成ではフック到達性に注意する** — `enableDatabasePublicAccess: false` でも、azd を実行する端末が VNet にアクセスできていれば postprovision フックは成功する。到達できない場合はフックが警告を出して正常終了し、VNet 内から別途プリンシパルを作成する。実際の作成手順は [azd-hooks スキル](../azd-hooks/SKILL.md) を参照

## PostgreSQL Flexible Server の repo 固有メモ

汎用的な Bicep パターン（`authConfig`、`administrators`、認証方式の選択など）は AVM と Microsoft Learn を参照すること。ここにはこの repo で繰り返し踏みやすい点だけ残す。

- **Entra 管理者設定は `dependsOn` を明示する** — 開発者 IP 用ファイアウォール規則と `postgresDatabase` の後でないと accessible にならず失敗することがある
- **`0.0.0.0` ファイアウォール規則（AllowAllAzureServicesAndResourcesWithinAzureIps）は使わない** — この規則は**他テナントの Azure リソースからも接続を許可**してしまう。開発者が psql で直接接続するには、開発者の IP アドレスをパラメータ（例: `developerIpAddress`）で受け取り、明示的なファイアウォール規則を作成する。postprovision フックの一時ファイアウォール規則と役割を混同しないこと

## App Service Python の可観測性

- **`ApplicationInsightsAgent_EXTENSION_VERSION: ~3` を appSettings に含める** — Python on Linux App Service では `APPLICATIONINSIGHTS_CONNECTION_STRING` だけではテレメトリが収集されない。`ApplicationInsightsAgent_EXTENSION_VERSION` を `~3` に設定して初めて自動計装エージェントが有効になる
- **psycopg (v3) の DB 依存関係テレメトリには OTel パッケージが必要** — 自動計装が自動検出するのは `psycopg2` のみ。psycopg v3 を使う場合は `opentelemetry-instrumentation-psycopg` を `pyproject.toml` の依存に追加すること。App Service はインストール済みの OTel インストルメンテーションを自動検出する

詳細は [references/azd-infra-rules.md](references/azd-infra-rules.md) の「App Service Python の可観測性」セクションを参照。

## App Service のセキュリティ必須設定

- **SCM / FTP 基本認証を無効化する** — azd は Entra ID 認証でデプロイするため、発行資格情報（基本認証）は不要。`basicPublishingCredentialsPolicies` で `scm` と `ftp` の両方を `allow: false` に設定すること。`ftpsState: 'Disabled'` だけでは SCM 基本認証は無効にならない（独立した制御）

## App Service Python デプロイの必須チェック

アプリコード生成・Bicep 変更時は [references/azd-infra-rules.md](references/azd-infra-rules.md) の「App Service Python アプリのデプロイ」セクションを確認すること。

## Validation

Bicep ファイルを追加・変更したら、少なくともビルド検証を実行すること。

```shell
az bicep build --file <file>
```
