# azd 前提 IaC ルール

このリポジトリは Azure Developer CLI (azd) 構成であり、Bicep / hooks / `azure.yaml` が `azd up` で一貫して動作する構造にする。

## targetScope

`subscription` スコープにし、リソースグループの作成をテンプレート内に含める。azd は subscription レベルデプロイを前提とする。

```bicep
targetScope = 'subscription'

resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${workloadName}-${environmentName}'
  location: location
  tags: tags
}
```

## azd 標準パラメータ

| パラメータ | 説明 | 備考 |
|-----------|------|------|
| `environmentName` | azd が自動設定する環境名 | 必須。デフォルト値は設定しない |
| `location` | リソースのデプロイ先リージョン | 必須 |

### `environmentName` の命名規則

`environmentName` はリソース名に組み込まれるため（例: `app-myproj-${environmentName}`）、**用途を示す短い名前**にする。azd のデフォルト（ディレクトリ名）は冗長になりやすいため、明示的に指定すること。

```shell
# 推奨: 短く意味のある名前
azd init -e poc
azd init -e dev
azd init -e prod

# 非推奨: デフォルトのディレクトリ名（冗長）
azd init  # → azure-lifecycle-with-copilot-cli
```

## パラメータファイル形式

azd は `main.parameters.json`（JSON 形式）と `main.bicepparam`（Bicep パラメータ形式）の両方をサポートする。

### このプロジェクトでは `main.parameters.json`（JSON 形式）を使う

**判断基準:**

| 観点 | `.bicepparam` | `main.parameters.json` |
|------|--------------|----------------------|
| 型安全・エディタ補完 | ✅ `using` で bicep にリンク | ❌ スキーマ補完のみ |
| 式・変数の利用 | ✅ `var`, 関数が使える | ❌ 文字列置換のみ |
| `@minLength` との相性 | ⚠️ `readEnvironmentVariable` のデフォルト値がビルド時に制約評価される | ✅ プレースホルダーは azd が実行時に置換するため衝突しない |
| azd テンプレート実績 | △ 新しい形式 | ✅ 公式テンプレートの大半が採用 |

**このプロジェクトで JSON を選ぶ理由:**

1. **ラボ教材として公式テンプレートとの一貫性を優先** — 受講者が他の azd サンプルを参照しやすい
2. **`@minLength(1)` を維持できる** — Bicep 単体でのバリデーションが効き、パラメータ不備を早期検出
3. **`readEnvironmentVariable` + `@minLength` 衝突の罠を回避** — ラボ受講者が踏む必要のない地雷

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environmentName": { "value": "${AZURE_ENV_NAME}" },
    "location": { "value": "${AZURE_LOCATION}" }
  }
}
```

デフォルト値付きの変数は `${VAR_NAME=default}` 構文で指定する。

### preprovision フックが設定するパラメータのデフォルト値

Copilot CLI の bash は非 TTY のため、`azd up` / `azd provision` 実行時にパラメータ検証が preprovision フック実行前に走る。フックが `azd env set` で設定するパラメータ（`pgAdminObjectId`、`pgAdminLoginName`）に `main.parameters.json` でデフォルト値がないと、検証段階で `missing required inputs` エラーになる。

**対策**: フックが設定するパラメータには必ずプレースホルダーのデフォルト値を付ける。

```json
{
  "pgAdminObjectId": { "value": "${pgAdminObjectId=pending}" },
  "pgAdminLoginName": { "value": "${pgAdminLoginName=pending}" }
}
```

デフォルト値 `pending` は検証通過のためだけに存在し、preprovision フックが実行後に実際の値で上書きする。Bicep デプロイには上書き後の値が使われる。

### `azd env set` で制御するパラメータのマッピング

Bicep パラメータにデフォルト値がある場合でも、`azd env set` で値を上書きしたい場合は `main.parameters.json` にマッピングが必要。マッピングがないと、`azd env set` で設定した値は Bicep に渡らず、常に Bicep 側のデフォルト値が使われる。

```json
{
  "enableDatabasePublicAccess": { "value": "${enableDatabasePublicAccess=false}" }
}
```

**よくある誤解**: 「Bicep にデフォルト値があるから `main.parameters.json` に書かなくてよい」→ Bicep 単体ではその通りだが、`azd env set` による実行時の上書きが効かなくなる。`azd env set` での制御を想定するパラメータは、Bicep のデフォルト値と同じ値を `main.parameters.json` のデフォルトに設定しておくこと。

### `.bicepparam` を選ぶべきケース（参考）

- パラメータ値に式やロジックが必要な場合（`toLower()`, 条件分岐等）
- エディタでの型安全な補完を重視する場合
- `@minLength` を使わない設計の場合

ただし `readEnvironmentVariable` のデフォルト値はビルド時に `@minLength` 等の制約で評価されるため、`@minLength(1)` のパラメータにデフォルト `''` を渡すとビルドエラーになる点に注意。

## azd タグ

- リソースグループに `azd-env-name` タグを付与（値は `environmentName`）
- `azure.yaml` の `services` に対応するホストリソース（App Service 等）に `azd-service-name` タグを付与

azd はこれらのタグを使ってリソースを検出し、デプロイ先を決定する。

## グローバル一意リソースの命名

App Service や PostgreSQL Flexible Server はホスト名がグローバル一意である必要がある。公開ラボで複数ユーザーが同じ環境名を使っても衝突しないよう、`uniqueString()` 由来のサフィックスを付与する。

```bicep
// main.bicep
var resourceToken = substring(uniqueString(subscription().subscriptionId, environmentName, location), 0, 5)
```

- **サフィックスを付けるリソース** — App Service、PostgreSQL Flexible Server（ホスト名がグローバル一意）
- **サフィックスを付けないリソース** — リソースグループ、App Service Plan、Log Analytics、Managed Identity、VNet（RG 内またはサブスクリプション内で一意であれば十分）

```bicep
// グローバル一意が必要
name: 'app-${workloadName}-${environmentName}-${resourceToken}'   // App Service
name: 'psql-${workloadName}-${environmentName}-${resourceToken}'  // PostgreSQL

// グローバル一意が不要
name: 'rg-${workloadName}-${environmentName}'     // Resource Group
name: 'plan-${workloadName}-${environmentName}'    // App Service Plan
name: 'log-${workloadName}-${environmentName}'     // Log Analytics
```

## Bicep 出力とフック変数の契約

フックスクリプトや `azure.yaml` で参照する環境変数は、`main.bicep` の `output` に明示すること。azd は Bicep 出力を環境変数として引き渡す。

`AZURE_RESOURCE_GROUP` は azd が自動提供しないため、必要なら output に含める。

```bicep
output AZURE_RESOURCE_GROUP string = rg.name
```

## SKU とリソース機能の整合性

ゾーン冗長など、SKU によって利用可否が異なる機能はパラメータ化し、SKU に合わない組み合わせにならないようにする。

例: B1 SKU ではゾーン冗長は非対応。`appServicePlanZoneRedundant` パラメータで制御し、デフォルトは `false`。

## App Service SKU

Python を App Service でリモートビルドする際には、ビルドがタイムアウトしないよう Premium プランを基本とする。

## App Service Python の可観測性

### 自動計装の有効化（Bicep 側）

App Service Python (Linux) で Application Insights の自動計装を使うには、以下の **2 つ**のアプリ設定が必要:

```bicep
appSettings: [
  {
    name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
    value: appInsights.properties.ConnectionString
  }
  {
    name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
    value: '~3'
  }
]
```

`APPLICATIONINSIGHTS_CONNECTION_STRING` だけではテレメトリは一切収集されない。`ApplicationInsightsAgent_EXTENSION_VERSION: ~3` が自動計装エージェントの起動トリガーになる。

### DB 依存関係の収集（アプリ側）

自動計装エージェントが自動検出するライブラリは限られている:

| ライブラリ | 自動検出 | 備考 |
|-----------|---------|------|
| `psycopg2` | ✅ | レガシードライバ |
| `psycopg` (v3) | ❌ | OTel パッケージの追加が必要 |
| `requests`, `urllib`, `urllib3` | ✅ | |
| `Django`, `FastAPI`, `Flask` | ✅ | |

psycopg v3 で DB 依存関係テレメトリを収集するには、`opentelemetry-instrumentation-psycopg` を `pyproject.toml` の依存に追加する:

```toml
dependencies = [
    "psycopg[binary]>=3.2",
    "opentelemetry-instrumentation-psycopg>=0.50b0",
]
```

App Service はデプロイ時のリモートビルドでインストールされた OTel インストルメンテーションパッケージを自動検出する。アプリコードの変更は不要。

> **背景**: Microsoft Learn の「[Monitor Azure App Service](https://learn.microsoft.com/azure/azure-monitor/app/monitor-azure-app-service)」に記載:「*To collect telemetry from other libraries, add supported OpenTelemetry community instrumentation packages to your app's requirements.txt file. App Service detects installed instrumentations automatically.*」

### psycopg v3 の async は自動計装と非互換になりやすい

**事象**: `psycopg.AsyncConnection` でクエリを実行すると、App Service のワーカーが `AttributeError: 'CursorTracer' object has no attribute 'traced_execution_async'` を投げて失敗する。

**原因**: App Service Linux の自動計装エージェントはエージェント側にバンドルされた `opentelemetry-instrumentation-dbapi` を先にロードする。pip 側でインストールした新しい `opentelemetry-instrumentation-psycopg`（0.50b0+）は親クラスに `traced_execution_async` があることを前提にしているが、バンドル版 dbapi が古く、このメソッドが存在しない。結果として async パスが全滅する。

**回避策（推奨）**: `psycopg.AsyncConnection` を使わず、**同期 `psycopg.connect` を `asyncio.to_thread` でラップ**する。sync 側の `traced_execution` は古いバンドル dbapi にも存在するため、DB 依存関係テレメトリが取得できる。

```python
import asyncio
import psycopg
import psycopg.conninfo  # サブモジュールを明示 import しないと make_conninfo が参照できない

def _query_sync(conninfo: str) -> tuple:
    with psycopg.connect(conninfo, connect_timeout=5) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version(), current_database(), current_user, now()")
            return cur.fetchone()

async def check_db(conninfo: str) -> tuple:
    return await asyncio.to_thread(_query_sync, conninfo)
```

**非推奨**: `OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=psycopg` で無効化する方法は一見動作するが、DB 依存関係テレメトリ自体が失われるため恒久策にしない。

## App Service Python アプリのデプロイ

### 起動コマンド (`appCommandLine`)

App Service Python (Linux) は gunicorn を自動起動する。自動検出の優先順位は:

1. カスタム起動コマンド（`appCommandLine`）
2. Django（`wsgi.py` を検出）
3. Flask 系（`application.py`, `app.py`, `index.py`, `server.py` を検出）
4. デフォルトアプリ

FastAPI (ASGI) は自動検出されないため、`appCommandLine` で明示的に設定すること。

#### ❌ `uvicorn` を直接呼び出してはいけない

`requirements.txt` や `uv.lock` でインストールしたパッケージのコマンドは**直接呼び出せない**。これは [MS Learn](https://learn.microsoft.com/azure/developer/python/configure-python-web-app-on-app-service) に明記されている:

> 「web servers installed via requirements.txt aren't added to the Python global environment and therefore **can't be invoked directly**. You use `python -m` because the `python -m` command invokes the server from within the current virtual environment.」

**根本原因**: App Service のビルドコンテナとランタイムコンテナはパスが異なる。ランタイムは venv の activate ではなく PYTHONPATH 経由で site-packages を参照する設計のため、venv の `bin/` が PATH に乗らない（[Oryx scriptgenerator.go](https://github.com/microsoft/Oryx/blob/main/src/startupscriptgenerator/src/python/scriptgenerator.go) のコメント参照）。この制約は uvicorn 固有ではなく celery、alembic 等すべての venv パッケージに当てはまる。

#### 正しい起動コマンド

**方法1: gunicorn 経由（推奨）** — gunicorn はランタイムイメージにプリインストール済みのため直接呼び出せる。PYTHONPATH 経由で venv の `uvicorn.workers` を import できる。

```bicep
siteConfig: {
  appCommandLine: 'gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app'
}
```

**方法2: `python -m` 経由** — `python -m` は sys.path（PYTHONPATH を含む）からモジュールを検索するため動作する。

```bicep
siteConfig: {
  appCommandLine: 'python -m uvicorn main:app --host 0.0.0.0 --port 8000'
}
```

> **注意**: プリインストール済み gunicorn のバージョンは Microsoft 管理。バージョンを固定したい場合は `pyproject.toml` の依存に gunicorn を追加し、venv 内のものを `python -m gunicorn` で使う。

> **⚠️ siteConfig の注意**: Bicep から `appCommandLine` 等のプロパティを削除しても、App Service の siteConfig では既存の値が保持される場合がある。値を変更する場合は新しい値で明示的に上書きすること。

### リモートビルドの有効化

Python アプリでは `SCM_DO_BUILD_DURING_DEPLOYMENT=true` を appSettings に含めること。これがないとリモートビルドが実行されず、依存パッケージがインストールされない。

### pyproject.toml と uv

- **`[build-system]` セクションは含めない** — App Service + uv 環境では virtual project（依存のみ、パッケージとしてビルドしない）として扱う。`[build-system]` があると hatchling 等がパッケージディレクトリを探して失敗する
- `pyproject.toml` + `uv.lock` の規約は `copilot-instructions.md` を参照

## PostgreSQL のネットワーク

VNet・App Service VNet 統合・PostgreSQL Private Endpoint は常に作成される（PoC・本番共通）。`enableDatabasePublicAccess` パラメータ（bool）で PostgreSQL のパブリックアクセスのみを制御する。**デフォルト値は `false`（Secure-by-default）。** PoC では `azd env set enableDatabasePublicAccess true` で明示的に有効化する。

| 設定項目 | enableDatabasePublicAccess=true (PoC) | enableDatabasePublicAccess=false (本番) |
|---------|---------------------------------------|----------------------------------------|
| VNet・サブネット | ✅ 作成 | ✅ 作成 |
| App Service VNet 統合 | ✅ 有効 | ✅ 有効 |
| PostgreSQL PE | ✅ 作成 | ✅ 作成 |
| Private DNS Zone | ✅ 作成 | ✅ 作成 |
| DB パブリックアクセス | ✅ 有効（開発者 IP の FW ルール付き） | ❌ 無効 |

Bicep 内で `publicNetworkAccess` を導出し、独立パラメータにしない。詳細は [azd-infra-rules SKILL.md](../SKILL.md) を参照。

### PoC 用ファイアウォール規則

PoC モードでは開発者が psql で直接接続できるよう、**明示的な開発者 IP アドレス**をパラメータで受け取りファイアウォール規則を作成する。`0.0.0.0`（AllowAllAzureServicesAndResourcesWithinAzureIps）は他テナントの Azure リソースにも接続を許可してしまうため使用禁止。

```bicep
@description('PoC 用: 開発者のパブリック IP アドレス（enableDatabasePublicAccess=true 時のみ有効）')
param developerIpAddress string = ''

resource postgresFirewallDeveloper '...' = if (enableDatabasePublicAccess && !empty(developerIpAddress)) {
  parent: postgresServer
  name: 'AllowDeveloper'
  properties: {
    startIpAddress: developerIpAddress
    endIpAddress: developerIpAddress
  }
}
```

> **注意**: postprovision フックが使う一時ファイアウォール規則とは別物。フックは実行時に自身の IP を取得し、try/finally で一時規則を作成・削除する。Bicep 側の規則は開発者が手動で psql 接続するための常設規則。

### App Service のセキュリティ必須設定

SCM / FTP 基本認証を無効化する。azd は AAD 認証でデプロイするため、発行資格情報は不要。`ftpsState: 'Disabled'` だけでは SCM 基本認証は無効にならない。

```bicep
resource scmBasicAuth 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-04-01' = {
  parent: appService
  name: 'scm'
  properties: { allow: false }
}

resource ftpBasicAuth 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-04-01' = {
  parent: appService
  name: 'ftp'
  properties: { allow: false }
}
```

## PostgreSQL Flexible Server の Entra ID ユーザー作成

Bicep では Managed Identity 名をフックに渡すための `output` を定義する。フックでの実際のユーザー作成手順は [azd-hooks スキル](../../azd-hooks/SKILL.md) および [postgresql-entra-id-provisioning.md](../../azd-hooks/references/postgresql-entra-id-provisioning.md) を参照。

```bicep
// resources.bicep
output managedIdentityName string = managedIdentity.name

// main.bicep
output MANAGED_IDENTITY_NAME string = resources.outputs.managedIdentityName
```

## 診断設定を追加する前の事前確認

`Microsoft.Insights/diagnosticSettings` は拡張リソースのため、**Bicep ビルド（`az bicep build`）・ARM テンプレート検証・What-If では親リソースの適合性を検知できない**。対象 RP がカテゴリを公開していない場合、実デプロイ時に初めて `ResourceTypeNotSupported` で失敗する。

**典型的な非対応リソース**:

- `Microsoft.Network/privateEndpoints` — 診断カテゴリなし（NIC 側で取る）
- `Microsoft.Network/privateDnsZones` — 非対応
- `Microsoft.Storage/storageAccounts` 本体 — サブリソース（`blobServices` 等）で個別に設定する

**手順**:

1. 診断設定を Bicep に書く前に [Supported categories for Azure Monitor resource logs](https://learn.microsoft.com/azure/azure-monitor/essentials/resource-logs-categories) で対象リソース種別の掲載を確認する
2. 掲載されていない場合は診断設定を付けない。代替手段（NIC、NSG Flow Logs、Network Watcher、上位/サブリソースでの設定等）を検討する
3. 迷ったら dev / poc 環境に先に当てて RP の応答で確認する（検証用リソースグループを小さく回すほうが What-If に頼るより確実）

**静的に検知できない理由**:

`Microsoft.Insights/diagnosticSettings` は `scope: 任意の ARM リソース` を受け付ける拡張リソース。Bicep コンパイラは ARM スキーマだけを検証し、親 RP が `GET /providers/microsoft.insights/diagnosticSettingsCategories` で何を返すかは知らない。適合性は RP が実行時に決める。

## ログ取り込みコストの最適化

ログの取り込みコスト削減が要件にある場合に検討する項目をまとめる。コスト要件がない場合はこのセクションの適用は不要。

### 1. 診断設定のカテゴリ絞り込み

`categoryGroup: 'allLogs'` は全ログカテゴリを送信するため、データ量が大きくなる可能性がある。コスト重視の場合は、コアカテゴリのみ個別に有効化する:

**App Service — コアカテゴリ:**

- `AppServiceHTTPLogs`、`AppServiceAppLogs`、`AllMetrics`

**PostgreSQL Flexible Server — コアカテゴリ:**

- `PostgreSQLLogs`、`AllMetrics`

追加カテゴリ（`PostgreSQLFlexSessions`、`PostgreSQLFlexQueryStoreRuntime` 等）はトラブルシューティング時に有効化する運用とすることで、取り込みコストを抑えられる。

> **Azure Policy との衝突**: サブスクリプションの Azure Policy が `categoryGroup: 'allLogs'` で診断設定を自動作成する場合がある。Policy が管理する診断設定名（例: `diag-postgres`）と同じ名前を Bicep で定義すると Bicep 側の設定で上書きできるが、Policy が再適用すると戻る可能性がある。**Policy の構成を変更できない場合は Policy を優先**し、Bicep 側の診断設定は Policy と同じ構成に合わせること。

### 2. Basic テーブルプラン

Log Analytics ワークスペースのテーブルには Analytics（既定）と Basic の 2 つのプランがある。Basic は取り込みコストが低い代わりに、クエリ機能が制限される（8 日間保持、KQL の一部機能のみ）。頻繁にクエリしないテーブルに適する。

**前提条件**: Basic プランはリソース固有テーブル（resource-specific mode）でのみ有効。診断設定の `logAnalyticsDestinationType` が `AzureDiagnostics`（レガシー）の場合、全ログが `AzureDiagnostics` テーブルに集約され、テーブル単位のプラン設定ができない。

**このリポジトリのサービスで Basic 対応のテーブル:**

| サービス | Basic 対応テーブル |
|---------|-------------------|
| PostgreSQL Flexible Server | `PGSQLServerLogs`, `PGSQLQueryStoreRuntime`, `PGSQLQueryStoreWaits`, `PGSQLPgStatActivitySessions`, `PGSQLDbTransactionsStats`, `PGSQLAutovacuumStats` |
| Application Insights | `AppTraces` |
| App Service | なし（`AzureMetrics` のみ） |

参照: [Tables that support the Basic table plan](https://learn.microsoft.com/azure/azure-monitor/logs/basic-logs-azure-tables)

**Bicep での設定例:**

```bicep
resource pgLogsTable 'Microsoft.OperationalInsights/workspaces/tables@2022-10-01' = {
  parent: logAnalytics
  name: 'PGSQLServerLogs'
  properties: {
    plan: 'Basic'
  }
}
```

> **注意**: テーブルは診断設定からデータが流れ始めた後に作成される。初回デプロイ時はテーブルが存在せず失敗する場合がある。postprovision フックや 2 回目以降のデプロイで設定するか、`az monitor log-analytics workspace table update --plan Basic` で手動設定する運用も検討すること。
