# Microsoft Azure PowerPoint Template (Light)

このプロジェクトでは Azure 公式テンプレート（`.potx`）を使用する。

## テンプレートファイル

- `.github/skills/azure-pptx/assets/Microsoft-Azure-PowerPoint-Template-Light.potx`
- python-pptx は `.potx` を直接開けないため、`[Content_Types].xml` のコンテンツタイプを `.pptx` 相当に書き換えてから読み込む必要がある
- テンプレートには55枚以上のサンプルスライドが含まれるため、新規スライド追加前にすべて削除すること

## Fonts

- **テーマ定義済み**: 見出し = Segoe Sans Text Semibold / Yu Gothic UI Semibold、本文 = Segoe Sans Text / Yu Gothic UI
- python-pptx でテキストを追加する際は、テーマフォント参照を使うか、上記フォント名を明示指定
- `<a:latin typeface="Yu Gothic UI Semibold"/>` / `<a:ea typeface="Yu Gothic UI Semibold"/>` (見出し)
- `<a:latin typeface="Yu Gothic UI"/>` / `<a:ea typeface="Yu Gothic UI"/>` (本文)

## Font Sizes

テンプレートのレイアウトに定義済みのサイズに従うこと。明示指定する場合は以下を基準とする:

| レイアウト | 要素 | サイズ |
|-----------|------|--------|
| Title Slide / Demo / Section Title | タイトル | 40pt |
| Title Slide / Demo | サブタイトル・本文 | 16pt |
| Title and Content / Two Column | タイトル | 40pt (テーマ継承) |
| Title and Content / Two Column | 本文 | 18pt (デフォルト 17.65pt) |
| Three Column | 小見出し | 22pt |
| Three Column | 本文 | 20pt (level1), 18pt (level2) |
| Five Column | 小見出し | 16pt |
| Five Column | 本文 | 15pt (level1), 14pt (level2) |

**重要**: テンプレートの定義サイズを上書きしない。

## レイアウトインデックス

テンプレートのスライドレイアウトは `prs.slide_layouts[index]` で参照する。

| Index | レイアウト名 | プレースホルダ |
|-------|-------------|---------------|
| 2 | Title Slide | ph0=タイトル, ph12=サブタイトル |
| 12 | Title and Content | ph0=タイトル, ph10=ボディ |
| 14 | Two Column Bullet | ph0=タイトル, ph12=左ボディ, ph13=右ボディ |
| 16 | Two Column Bullet with Subheads | ph0=タイトル, ph16=左小見出し, ph17=右小見出し, ph14=左ボディ, ph15=右ボディ |
| 18 | Three Column with Subtitles | ph0=タイトル, ph16-18=小見出し, ph14-15/19=ボディ |
| 42 | Title and Text Side by Side | ph0=タイトル, ph11=ボディ |
| 49 | Demo | ph0=タイトル, ph12=ボディ |
| 50 / 52 / 53 | Section Title (バリエーション) | ph0=タイトル |
| 65 | Thank You | ph0=タイトル, ph12/ph13=補助テキスト |

**注意**: インデックスはテンプレートのバージョンにより変わる可能性がある。初回利用時に `thumbnail.py` や XML 調査で確認すること。

### 📌 クロージングスライド

- 裏表紙・締めスライドが必要な場合は、まず **Thank You** レイアウト（index 65）を使えるか確認する
- このレイアウトで十分な場合、独自の closing slide を別途デザインしない
- `Thank you` だけで成立する場面では、ph12 / ph13 は空でもよい

## Bullet Points

- 箇条書きプレースホルダ（Content / Body 等）を使う場合、テキストに手動の箇条書き記号（`• ` `・ ` `- ` 等）を**付けないこと**
- プレースホルダ自体がビュレット書式を持っているため、記号を付けると二重表示になる
- 空行（`""`）を項目に含めないこと。空パラグラフにもビュレットが表示されてしまう
- **非箇条書きテキストを入れる場合、`<a:buNone/>` を追加してビュレット継承を抑止すること**

## 図形

- 四角形は角丸なし（`MSO_SHAPE.RECTANGLE`）を使うこと。`ROUNDED_RECTANGLE` は使わない

## 構成図・大型図の埋め込み

- **図が 1 スライドで読めない場合は、無理に埋め込まず別資料参照に切り替える**
- 大型画像（構成図等）は **Title Only レイアウト** を使う
- タイトルはレイアウトのプレースホルダを継承し、位置・サイズ・色を手動指定しない
- **画像の実際のピクセルサイズを読み、アスペクト比を保って配置すること**
- Windows で draw.io CLI から PNG を作る場合、直接実行で出力が不安定なら `Start-Process -Wait` で export する
- draw.io の exported PNG を `python-pptx` / Pillow が読めない場合がある。その場合は `System.Drawing.Image.Save(..., Png)` などで一度 **標準 PNG として再保存** してから埋め込む
- 構成図を大きく見せたい場合、draw.io 側の `border` を必要最小限まで減らし、PowerPoint 側でもタイトル直下まで使って配置する
- 構成図や大型図が主役のスライドでは、**図自体で読める場合に限り**、画像下の補足コメントを最小限にする
- 図だけでは理解しづらい場合は、同一スライドに短い注釈を足すか、説明用スライドを別に設ける
- 「概要図は別資料を参照」とする場合は、スライド側にファイル名や参照先（例: `docs/design-infrastructure-diagram.drawio`）を明記する

## 言語設定

- スライドコンテンツの言語はプロジェクトの `.github/copilot-instructions.md` で定義する
- `<a:rPr>` に適切な `lang` 属性を設定すること
