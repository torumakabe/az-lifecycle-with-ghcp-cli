# ラボ3: Azure構成図の生成
**テーマ**: Bicep から構成図を自動生成する

## 前提条件

- [ラボ環境セットアップガイド](./setup/README.md)を完了していること
- ラボ2（Bicep作成）が完了し、`infra/` にBicepファイルが存在すること

## シナリオ

ラボ2で作成した Bicep ファイルから、Azure 構成図を自動生成する。
Mermaid 形式と draw.io 形式の2種類を試し、それぞれの特徴を確認する。

構成図は `docs/` ディレクトリに出力する（ドキュメントは IaC + ADR から生成する出力物という方針）。

---

## ステップ1: Mermaid 構成図の生成

**Copilot CLIに入力:**

```
@infra/ このBicepファイルからAzure構成図を Mermaid形式で docs/design-infrastructure-diagram.md に作って。本番環境だけでなく、全ての環境を。後続のドキュメントやスライドから参照しやすいよう、可読性を優先し、必要なら分割して
```

**期待する結果:**

- `infra/` 配下の Bicep ファイルが解析され、リソース間の依存関係が Mermaid 構文で表現される
- `docs/design-infrastructure-diagram.md` に構成図が保存される
- Bicep で定義された構成要素とその接続関係が図示される

> [!IMPORTANT]
> - リソース間の接続関係が Bicep の定義と一致しているか確認する

---

## ステップ2: draw.io 構成図の生成

**Copilot CLIに入力:**

```
@infra/ このBicepファイルからAzure構成図を draw.io 形式で docs/design-infrastructure-diagram.drawio に作って。本番環境だけでなく、全ての環境を。後続のドキュメントやスライドから参照しやすいよう、1ページに無理に詰め込まず必要なら分割して
```

> [!NOTE]
> 時間がかかる。

**期待する結果:**

- azure-drawio Skill が呼ばれ、公式 Azure アイコン付きの構成図が生成される
- `docs/design-infrastructure-diagram.drawio` として保存される
- draw.io Desktop、VS Code draw.io 拡張、または draw.io Web で開いて編集できる

> [!IMPORTANT]
> - draw.io ファイルを開いて、アイコンとレイアウトが正しいか確認する
> - 手動で位置やグループを調整できることを確認する

---

## まとめ

- **Mermaid 形式**: Markdown 埋め込み対応、テキストベースで差分が見やすい
- **draw.io 形式**: azure-drawio Skill で公式アイコン付き、GUIで編集可能

---

**次のラボ:** [ラボ4: コスト見積もり](./04-cost-estimation.md)
