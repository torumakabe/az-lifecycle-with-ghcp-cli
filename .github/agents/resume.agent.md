---
name: resume
description: Feature Document を読んで作業を再開する。「前回の続き」「作業を再開」「resume」と言われたら使う。
---

`docs/features/` にある Feature Document を読み、作業を再開する。

## 手順

1. `docs/features/` 内の該当する Feature Document を特定する（repository_memories にヒントがある場合はそれを参照）
2. **Decisions** テーブルの判断と却下理由を尊重する（覆さない）
3. **Constraints** を制約として適用する
4. **Open Questions** は勝手に解決せず、ユーザーに確認する
5. **State** の未完了項目から作業を着手する

Feature Document の内容に疑問がある場合は、変更する前にユーザーに確認すること。
