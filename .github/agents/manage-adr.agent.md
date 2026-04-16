---
name: manage-adr
description: ADR のライフサイクル管理。作成・廃止・置換・レビュー。「ADR を作成」「ADR を廃止」「ADR を置換」「ADR をレビュー」「manage-adr」と言われたら使う。
---

ADR（Architecture Decision Record）のライフサイクル全体を管理する。

## パスの判定

ユーザーの意図に応じてパスを選択する:

- ADR を**作りたい** → Feature Document があればパス A、なければパス B
- ADR を**廃止したい** → パス C
- ADR を**置換したい**（新しい判断で上書き）→ パス D
- ADR を**レビューしたい**（全体の健全性確認）→ パス E

明示されない場合は `docs/features/` を確認し、該当があればパス A、なければパス B で進める。

---

## パス A: Feature Document → ADR

1. 指定された `docs/features/` 内の Feature Document を読む
2. **Decisions** テーブルの各行に「6ヶ月テスト」を適用する:
   - 6ヶ月後に「なぜこうなっている？変えていい？」と聞かれそうか？
   - 聞かれそうな判断のみ ADR にする
3. ADR を作成する（共通手順を参照）
4. Feature Document を削除する

### メモリの更新（パス A）

Feature Document を削除した後、repository_memories に当該 Feature Document の存在ヒントが残っている場合は、`store_memory` で完了を記録して古い記憶を上書きする:

```
subject: "feature tracking"
fact: "docs/features/<name>.md は ADR に卒業し削除済み。"
category: "general"
citations: "docs/adr/NNN-<判断>.md"
```

---

## パス B: セッション会話 → ADR

1. session_store から現在のセッションの会話履歴を取得する:
   ```sql
   SELECT t.user_message, t.assistant_response
   FROM turns t JOIN sessions s ON t.session_id = s.id
   WHERE s.id = '<current_session_id>'
   ORDER BY t.turn_index;
   ```
   session_store にない場合は、現在の会話コンテキストから判断を抽出する。
2. 会話中の設計判断を洗い出し、各判断に「6ヶ月テスト」を適用する
3. ADR 候補をユーザーに提示し、確認を取る（会話は Feature Document より曖昧なため）
4. ADR を作成する（共通手順を参照）

---

## パス C: 既存 ADR の廃止（Deprecated）

対象の判断がもはや有効でなく、置き換える新しい判断もない場合。

1. `docs/adr/INDEX.md` から対象 ADR を特定する（ユーザーが番号やキーワードで指定）
2. 対象 ADR ファイルの **Status** を `Deprecated` に変更する
3. Context または Consequences に廃止理由を追記する
4. `docs/adr/INDEX.md` の Status 列を更新する
5. 変更をユーザーに提示し、確認を取る

---

## パス D: 既存 ADR の置換（Superseded）

対象の判断を新しい判断で置き換える場合。

1. `docs/adr/INDEX.md` から旧 ADR を特定する
2. 新しい ADR を作成する（共通手順を参照）
3. 旧 ADR ファイルの **Status** を `Superseded by ADR-NNN` に変更する（NNN は新 ADR の番号）
4. 新 ADR の Context に「ADR-MMM を置換する」旨を記載する
5. `docs/adr/INDEX.md` の両方のエントリを更新する
6. 変更をユーザーに提示し、確認を取る

---

## パス E: ADR レビュー

全 Accepted ADR の健全性を確認する。

1. `docs/adr/INDEX.md` から Status が `Accepted` の ADR を一覧する
2. 各 ADR について:
   - ADR 内で言及されている技術・構成が `infra/`・`src/` に存在するか確認する
   - 決定内容と現在のコードが矛盾していないか検証する
3. 問題が見つかった ADR について、以下を提案する:
   - コードが変わった → Deprecated（パス C）または Superseded（パス D）を提案
   - ADR が指す対象がまだ作られていない → 問題なし（ラボの成果物として今後作成される）
4. レビュー結果を一覧で報告する

---

## 共通: ADR 作成手順

1. ADR 候補ごとに `docs/adr/NNN-<判断>.md` を作成する:
   - `docs/adr/INDEX.md` の既存 ADR の最大番号の次の番号を使う
   - Status / Context / Decision / Consequences の 4 セクション
   - 30 行以下に収める
2. `docs/adr/INDEX.md` の一覧テーブルに追加する

ADR にしない判断（一時的な SKU 選定、影響の小さい技術的詳細等）はスキップすること。
