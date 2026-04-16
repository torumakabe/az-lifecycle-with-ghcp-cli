# ラボ8: Azureリソース管理
**テーマ**: リソース状態の把握を自然言語で実行する

## 前提条件

- [ラボ環境セットアップガイド](./setup/README.md)を完了していること
- ラボ7（デプロイ）が完了し、Bicep で定義したリソースがデプロイ済みであること

## シナリオ

ラボ7でデプロイした Azure 環境に対して、実務で必要になる管理系の操作を Copilot CLI で行う。Resource Graph の KQL クエリ、Azure MCP Server を使った複数リソースの横断分析、複雑な Azure CLI コマンドの組み合わせなど、手作業では複数のツールとクエリ構文の知識が必要な操作を、自然言語で依頼する。

> [!NOTE]
> このラボは、ラボ1〜7の設計に依存しない。App Service と PostgreSQL Flexible Server がデプロイされていれば、構成の違い（ネットワーク構成、認証方式など）によらず実行できる。

---

## ラボ手順

### ステップ1: Resource Graph でセキュリティ露出面を分析

デプロイした環境のリソースを Resource Graph で横断的に検索し、インターネットへの露出状況を分類する。

> [!NOTE]
> Azure Resource Graph は、サブスクリプション内の全リソースの構成を KQL で横断検索できるサービス。リソースタイプごとに公開設定のプロパティ名が異なるため、手作業では各リソースのスキーマを調べて KQL を組み立てる必要がある。Copilot CLI は自然言語からこれを行ってくれる。

**Copilot CLIに入力:**
```
デプロイしたリソースグループ内で、インターネットからアクセスできる可能性があるリソースを調べて。Resource Graph を使って公開設定を確認し、リソースごとにどのように露出しているか分類して
```

**期待する動作の例:**
- Azure MCP Server でリソースグループ名を特定
- `az graph query` で KQL クエリを生成・実行（例: `resources | where resourceGroup =~ '...' | project name, type, properties.publicNetworkAccess, ...`）
- リソースごとの公開状態を分類して報告（例: App Service は HTTPS で公開、PostgreSQL は Public Network Access が有効/無効）

> [!TIP]
> 設計判断によって結果は変わる。たとえば PostgreSQL の Public Network Access が有効でも、ファイアウォール規則や Entra ID 認証で保護されている場合がある。Copilot CLI がどのように構成全体を解釈するか観察しよう。

---

### ステップ2: App Service → PostgreSQL の接続構成を横断分析

App Service から PostgreSQL への接続がどのように構成されているかを、複数のリソース設定を横断して分析する。

> [!NOTE]
> App Service がどのように PostgreSQL に接続するかを把握するには、App Service のアプリケーション設定（接続先ホスト名、DB名）、ネットワーク構成（VNet 統合やプライベートエンドポイントの有無）、PostgreSQL 側の公開設定やファイアウォール規則など、複数のリソースタイプの情報を突き合わせる必要がある。

**Copilot CLIに入力:**
```
App Service から PostgreSQL への接続がどのように構成されているか分析して。App Service のアプリケーション設定から接続先情報を確認し、ネットワーク経路（VNet統合やプライベートエンドポイントの有無、パブリックアクセスの設定）を調べて、接続経路の全体像を説明して
```

**期待する動作の例:**
- Azure MCP Server の `appservice` ツールでアプリケーション設定を取得（接続先ホスト名、DB名）
- Azure MCP Server の `postgres` ツールや Azure CLI で PostgreSQL のネットワーク設定を確認
- VNet 統合やプライベートエンドポイントが構成されている場合はその状態も確認
- 接続経路の全体像（パブリック経由 or プライベート経由）を説明

---

### ステップ3: 認証構成の追跡

App Service が PostgreSQL に接続する際の認証の仕組みを、複数のリソース設定を横断して追跡する。

> [!NOTE]
> PostgreSQL への認証方式は、Entra ID（Managed Identity）認証とパスワード認証がある。実際にどちらが使われているかを把握するには、App Service の ID 設定、アプリケーション設定の環境変数、PostgreSQL 側の認証構成をそれぞれ確認し、突き合わせる必要がある。

**Copilot CLIに入力:**
```
App Service が PostgreSQL にどのように認証して接続しているか追跡して。App Service に割り当てられた ID（Managed Identity やシステム割り当て ID）の有無と詳細、アプリケーション設定で接続先やユーザー名をどう参照しているか、PostgreSQL 側の認証方式の設定（Entra ID認証やパスワード認証の有効/無効）をそれぞれ確認して、認証の流れを説明して
```

**期待する動作の例:**
- Azure MCP Server の `appservice` ツールで ID 設定とアプリケーション設定を取得
- Azure CLI で Managed Identity の詳細（Client ID、Principal ID）を取得
- Azure MCP Server の `postgres` ツールや Azure CLI で認証構成（`authConfig`）を確認
- これらを組み合わせて認証フローの全体像を説明（例: App Service → Managed Identity → Entra ID トークン取得 → PostgreSQL、または接続文字列によるパスワード認証）

---

## まとめ

- Resource Graph の KQL で、リソース横断のセキュリティ分析を自然言語で実行した
- App Service → PostgreSQL の接続構成を、ネットワーク・アプリ設定・DB 設定を横断して分析した
- 認証チェーンを複数サービスの設定から追跡し、認証フローの全体像を可視化した
- いずれも手作業では複数のコマンド・ツール・クエリ構文の知識が必要だが、Copilot CLI は自然言語の依頼から適切なツールとクエリを選択・実行してくれる

---

**次のラボ:** [ラボ9: トラブルシューティング](./09-troubleshooting.md)
