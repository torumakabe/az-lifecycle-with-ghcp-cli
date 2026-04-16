# Copilot Instructions

## 言語

日本語で応答すること。生成するドキュメント（Markdown 等）も日本語で書くこと。

## プロジェクト概要

GitHub Copilot CLI が Azure のライフサイクル全体（設計・構築・デプロイ・運用）をどのように支援できるかを体験するハンズオンラボ。

## ディレクトリ構造

- `infra/` — Bicep テンプレート（ラボ中に生成）
- `hooks/` — azd フック（Python、`uv run` で実行）
- `src/` — アプリコード（ラボ中に生成）
- `docs/` — ADR (`docs/adr/`)、調査レポート (`docs/research/`)、Feature Document (`docs/features/`)
- `lab/` — ラボとセットアップ

## 知識ソース

コード生成・技術選定・構成変更の際は `docs/adr/`（確定済み設計判断）と既存の `infra/`・`src/` を確認すること。

以下のファイルを読み書きする際は、対応するスキルの SKILL.md を**最初に**読むこと:

| ファイルパターン | スキル |
|---|---|
| `infra/**/*.bicep` | `.github/skills/azd-infra-rules/` |
| `hooks/**/*.py`, `azure.yaml` | `.github/skills/azd-infra-rules/` + `.github/skills/azd-hooks/` |
| `**/*.pptx` | `.github/skills/azure-pptx/` |
| `**/*.drawio` | `.github/skills/azure-drawio/` |

不確実な知識で試行錯誤する前に、MCP サーバーで公式ドキュメントを確認すること。

## 規約

- スクリプトは Python + `uv run` に一元化（`.sh`/`.ps1` の二重管理禁止）
- App Service Python アプリ（`src/`）の依存は `pyproject.toml` + `uv lock`。`requirements.txt` は作らない（Oryx が pip にフォールバックするため）
- App Service は Premium プランを原則とする（リモートビルド性能を考慮）

## デプロイ

`azd up` / `provision` / `deploy` の前に `.github/skills/azd-hooks/SKILL.md` と `.github/skills/azd-infra-rules/SKILL.md` を読むこと。`--no-prompt` は使わない。

## 事実検証

ドキュメントが「ADR-NNN で決定済み」等と主張している場合、`docs/adr/`・`docs/features/`・`infra/`・`src/` で実在を検証すること。
