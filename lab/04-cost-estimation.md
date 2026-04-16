# ラボ4: コスト見積もり
**テーマ**: Bicep から Azure リソースのコストを見積もり、SKU 比較や Excel 出力まで一気通貫で行う

## 前提条件

- [ラボ環境セットアップガイド](./setup/README.md)を完了していること
- ラボ2（Bicep作成）が完了し、`infra/` にBicepファイルが存在すること

## シナリオ

ラボ2で作成した Bicep ファイルを元に、Azure リソースのコスト見積もりを行う。
SKU の比較検討を経て、最終的に Excel ファイルとして `docs/` に出力する。

---

## ステップ1: コスト見積もりと SKU 比較

**Copilot CLIに入力:**

```
@infra/ このBicepファイルに定義されたAzureリソースの月額コストを見積もって。価格ツールを使って最新の価格で計算して
```

**期待する結果:**

- Azure MCP Server の Pricing Tool（`azure_development_get_prices`）が呼ばれる
- Bicep で定義された各リソースの月額コストが一覧表示される

> [!IMPORTANT]
> - Pricing Tool の呼び出しログで MCP 経由であることを確認する
> - 価格が妥当な範囲か概算で確認する

続けて、SKU を比較する:

**Copilot CLIに入力:**

```
App Service Plan を比較して。月額コストの差と、スペックの違い（CPU、メモリ、機能）を表にまとめて
```

**期待する結果:**

- スペック比較表が生成される（CPU コア数、メモリ、ディスク、自動スケール対応など）
- コスト差と機能差のトレードオフが明示される

---

## ステップ2: Excel 出力

**Copilot CLIに入力:**

```
ここまでの見積もり結果を Excel ファイルにまとめて docs/cost-estimate.xlsx に保存して。リソース名、SKU、月額コスト、年額コストの列を含めて
```

**期待する結果:**

- コスト見積もり結果が構造化された Excel ファイルとして `docs/cost-estimate.xlsx` に出力される
- リソース名、SKU、月額・年額コストの列が含まれる

> [!IMPORTANT]
> - Excel ファイルが期待通りの形式で生成されているか確認する
> - 数値が適切か確認する

---

## まとめ

- **Azure MCP Server 連携**: Pricing Tool で価格情報を取得
- **SKU 比較**: コストと機能を表形式で比較
- **Excel 出力**: 見積もり結果を `docs/` に保存
- **IaC 起点**: Bicep の定義からコストを算出

---

**次のラボ:** [ラボ5: PowerPoint スライドの生成](./05-presentation-generation.md)
