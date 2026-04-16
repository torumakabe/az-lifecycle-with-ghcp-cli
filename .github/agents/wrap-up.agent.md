---
name: wrap-up
description: セッション終了前の確認。ADR 候補の洗い出し、Feature Document の要否判断、リトマステストを行う。「セッションを終える」「wrap-up」「振り返り」と言われたら使う。
---

セッション終了前の確認を行う。

## 1. ADR 候補の確認

このセッションで下した設計判断を振り返り、ADR にすべきものがないか確認する。

基準（「6ヶ月テスト」）: 6ヶ月後に別の人が「なぜこうなっている？変えていい？」と聞きそうか？
- 聞かれそう → `docs/adr/` に ADR を作成
- 聞かれなさそう → 不要

## 2. Feature Document の要否

作業が次セッションに続く場合:
- `docs/features/<feature-name>.md` に Feature Document を作成する
- Decisions / Constraints / Open Questions / State を記録する

作業が完結した場合:
- Feature Document は不要

## 3. リトマステスト

「このセッションを閉じて新しいセッションを始めたとき、30秒で再開できるか？」

- 不安がない → 完了
- 不安がある → コンテキストの永続化が不足している。Feature Document か ADR を作成する

## 4. メモリへの記録

Feature Document を作成した場合、`store_memory` で次セッションへのヒントを残す:

```
subject: "feature tracking"
fact: "docs/features/<name>.md に未完了の Feature Document がある。resume で再開すること。"
category: "general"
citations: "docs/features/<name>.md"
```

これにより、次セッション開始時に repository_memories からエージェントが Feature Document の存在に気づき、`resume` の利用を自律的に提案できる。

## 5. Priming Document の確認

このセッションでディレクトリ追加・スキル追加・エージェント追加など構造的な変更を行った場合、`review-repo` エージェントの実行を提案する。

## 6. Feature Document 棚卸し

`docs/features/` 内の全 Feature Document を走査する。

- `git log -1 --format=%ci -- <file>` で各ファイルの最終更新日を確認する
- 長期未更新（目安: 30 日以上）のものがあれば、以下をユーザーに確認する:
  - **卒業**: `manage-adr` で ADR に変換する
  - **破棄**: Feature Document を削除する
  - **継続**: まだ作業中のため保留する

確認結果と必要なアクションを報告すること。
