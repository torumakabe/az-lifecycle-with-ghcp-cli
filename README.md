# Azure Lifecycle with Copilot CLI — 設計から運用までを体験するハンズオンラボ

GitHub Copilot CLI が Azure のライフサイクル全体（設計・構築・デプロイ・運用）をどのように支援できるかを体験するラボです。

> 以降、GitHub Copilot CLI を **Copilot CLI** と略記します。

## 前提条件

### 必須のツール

| ツール | 用途 | インストール確認 |
|--------|------|-----------------|
| [Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli) | ラボ実行・リポジトリ操作 | `copilot --version` |
| [Azure CLI](https://learn.microsoft.com/ja-jp/cli/azure/install-azure-cli) | Azure 操作 | `az version` |
| [Azure Developer CLI (azd)](https://learn.microsoft.com/ja-jp/azure/developer/azure-developer-cli/install-azd) | デプロイ | `azd version` |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Python スクリプト実行 | `uv --version` |
| [PostgreSQL クライアント (psql)](https://www.postgresql.org/download/) | PostgreSQL ユーザー作成 | `psql --version` |
| Azure CLI 拡張 `rdbms-connect` | `postprovision` フックが `az postgres flexible-server execute` で Entra プリンシパルを作成するために使用 | `az extension show --name rdbms-connect --query version -o tsv` |
| [draw.io Desktop](https://github.com/jgraph/drawio-desktop) | 構成図の編集・画像エクスポート | `drawio --version`（Windows: `& "C:\Program Files\draw.io\draw.io.exe" --version`） |

### 環境によって追加で必要なツール

| ツール | 対象環境 | 用途 | インストール確認 |
|--------|----------|------|-----------------|
| [PowerShell 7](https://learn.microsoft.com/ja-jp/powershell/scripting/install/installing-powershell) | Windows | `azd` フック実行 | `pwsh --version` |

### オプションのツール

スライド（PPTX）のビジュアル QA に使います。未導入でも PPTX の作成・編集は可能です。

| ツール | 用途 | インストール確認 |
|--------|------|-----------------|
| [LibreOffice](https://www.libreoffice.org/) | PPTX → PDF 変換 | `soffice --version` |
| [Poppler](https://poppler.freedesktop.org/) | PDF → 画像変換 | `pdftoppm -v` |

### 認証

`az login`、`azd auth login`、Copilot CLI の `/login` を済ませてください。

## 次のステップ

→ [lab/setup/README.md](lab/setup/README.md) でプラグインの導入とラボの準備へ進む

## 参考

このリポジトリの AI コラボレーション設計は、以下のコンセプトを参考にしています:

- [Knowledge Priming](https://martinfowler.com/articles/reduce-friction-ai/knowledge-priming.html) — AI にプロジェクト固有のコンテキストを事前共有する手法
- [Context Anchoring](https://martinfowler.com/articles/reduce-friction-ai/context-anchoring.html) — セッションを越えて設計判断を永続化する手法

これらのコンセプトを支える仕組みとして、以下のカスタムエージェント（`.github/agents/`）を用意しています:

| エージェント | 役割 |
|-------------|------|
| `manage-adr` | ADR のライフサイクル管理（作成・廃止・置換・レビュー） |
| `architecture-snapshot` | 現在の IaC と ADR からアーキテクチャ概要説明書を生成 |
| `resume` | Feature Document を読み、中断した作業を再開（ラボでは未使用） |
| `wrap-up` | セッション終了前の確認（ADR 候補の洗い出し、Feature Document の要否判断）（ラボでは未使用） |
| `review-repo` | リポジトリの整頓（instructions の鮮度、ADR/Feature Document の健全性チェック）（ラボでは未使用） |
