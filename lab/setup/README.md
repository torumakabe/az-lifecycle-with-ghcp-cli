# ラボ環境セットアップガイド

[README.md](../../README.md) のツールインストールと認証が完了している前提です。

## Copilot CLI セットアップ

リポジトリルートで Copilot CLI を起動し、以下の設定・確認を行います。

1. **Azure Skills プラグイン** — 初回のみ `/plugin marketplace add microsoft/azure-skills` でマーケットプレイスを登録し、`/plugin install azure@azure-skills` でインストールします。Azure MCP Server・各種スキルを含みます。全ラボで使用します。
2. **MS Learn MCP Server プラグイン** — `/plugin install microsoftdocs/mcp` でインストールします。公式 Microsoft ドキュメントの検索・参照に使用します。MS Learn MCP Server・各種スキルを含みます。全ラボで使用します。
3. **モデル選択** — `/model` でメインエージェントのモデルを選択します。このラボでの推奨は Claude Opus 4.6 です。Excel や PowerPoint の扱いに優れています。
4. **スキル確認** — `/skills list` でプロジェクトスキル `azure-pptx`、`azure-drawio`、`azd-infra-rules`、`azd-hooks`、`bicep-api-version-updater` およびプラグインで導入したスキルが有効であることを確認します。

## ラボの実行順序

ラボ1〜9は一連のストーリーです。ラボ10、11は独立して実行できます。

```
ラボ1 調査→ADR作成
  └→ ラボ2 IaC→Design Snapshot作成
       ├→ ラボ3 構成図作成
       ├→ ラボ4 コスト見積
       ├→ ラボ5 プレゼンテーション資料作成
       └→ ラボ6 検証アプリ作成
            └→ ラボ7 デプロイ
                 ├→ ラボ8 リソース管理
                 └→ ラボ9 トラブルシューティング

ラボ10 Bicep APIバージョン最新化（独立、ラボ2のBicepが必要）
ラボ11 Excel→IaC（独立）
```

準備ができたら [ラボ1](../01-research-and-design-decisions.md) から始めてください。

## クリーンアップ

> [!WARNING]
> ラボ後は Azure リソースを忘れずに削除してください。

```bash
uv run lab/setup/cleanup.py
```

Azure リソース削除（`azd down --force --purge`）とリポジトリ生成物の削除を一括で行います。確認プロンプトなしで実行するには `--yes` を付けます（`uv run lab/setup/cleanup.py --yes`）。

リポジトリの生成物削除は `git clean -fdx`（未追跡ファイル一括削除）と `git checkout -- .`（追跡ファイル復元）で行います。ファイル名のハードコードではなく、Git の追跡状態に基づくため、ラボで生成されるファイルの名前が変わっても対応できます。
