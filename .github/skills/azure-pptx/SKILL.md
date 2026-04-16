---
name: azure-pptx
description: "Use this skill any time a .pptx file is involved — as input, output, or both. This includes creating, reading, editing, or modifying presentations. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename. This project uses the Microsoft Azure PowerPoint Template (Light)."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX Skill

> **出自**: [Anthropic PPTX Skill](https://github.com/anthropics/skills/tree/main/pptx) をベースに、プロジェクト固有のルールを追加。  
> 「📌」マークのあるセクションは本リポジトリ専用のルールであり、ベーススキルには含まれない。

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `uv run python -m markitdown presentation.pptx` |
| Edit existing slides | Read [references/editing.md](references/editing.md) then [references/azure-template.md](references/azure-template.md) |
| Create new from template | [テンプレートから新規作成](#テンプレートから新規作成) — python-pptx でテンプレートを開き、不要スライドを削除して構築 📌 |
| Create from scratch | Read [references/pptxgenjs.md](references/pptxgenjs.md) **only when the user explicitly says template use is unnecessary** 📌 |

---

## Reading Content

```bash
# Text extraction
uv run python -m markitdown presentation.pptx

# Visual overview
uv run scripts/thumbnail.py presentation.pptx

# Raw XML
uv run scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [references/editing.md](references/editing.md) for full details.**

1. Analyze template with `thumbnail.py`
2. Unpack → manipulate slides → edit content → clean → pack

**This project uses the Azure template.** Read [references/azure-template.md](references/azure-template.md) for template-specific details (fonts, layout indices, placeholder mappings, bullet rules). 📌

### 📌 このプロジェクト固有の制約

- `.pptx` を新規作成・編集する場合、**Microsoft Azure PowerPoint Template (Light) の利用は必須**
- テンプレートを**使わずに**ゼロから組む案を、通常案として選んではならない
- **テンプレート未使用の `.pptx` を作った時点で、このプロジェクトでは要件未達**
- 「まずテンプレートなしで作って、あとで整える」という進め方も不可

> **補足: python-pptx / pptxgenjs の利用について**
>
> 上記で禁止しているのは「テンプレートを使わずにゼロから作る」ことであり、**ツール自体の利用ではない**。
>
> - ✅ python-pptx で **テンプレート .potx/.pptx を開いて** スライドを編集・追加・削除する → テンプレート利用
> - ❌ python-pptx で `Presentation()` を空から作る → テンプレート未使用
> - ❌ pptxgenjs で独自デザインのスライドを生成する → テンプレート未使用

### 📌 例外

次の場合に限り、テンプレート未使用案を検討してよい。

1. ユーザーがテンプレート不要と明示した場合
2. 既存テンプレートでは物理的に表現できず、代替案の検討をユーザーが明示的に求めた場合

上記以外では、**テンプレート未使用案を自分の判断で採用しない**。

### 📌 実装前チェック

スライド作成を始める前に、少なくとも次を確定すること。

1. どの Azure template layout を使うか
2. 画像中心のスライドか、画像 + 本文の併置か
3. 図表や外部画像を使う場合、それが 1 スライドで読めるか
4. 読めない場合、画像埋め込みを諦めて別資料参照に切り替えるか

この確認をせずに「作りやすい方法」で新規生成へ進まないこと。

### 📌 このリポジトリで得た運用メモ

- Azure template 固有のレイアウト選択、Thank you の使い方、draw.io 図の貼り込み方は **`references/azure-template.md`** に追記して管理する
- 概要図が大きすぎて 1 スライドで読めない場合、**図の貼り込みを必須にしない**。スライドには要点だけを載せ、図は別資料参照に切り替えてよい
- `SKILL.md` には「いつ template を使うか」「どういう順序で進めるか」の方針だけを書き、個別レイアウトの運用詳細は持ち込まない
- 初回出力をそのまま完成扱いにしない。`markitdown` と `soffice -> pdftoppm` の両方で内容と見た目を確認してから仕上げる

### 📌 テンプレートから新規作成

テンプレートをベースに新規プレゼンテーションを作る場合、XML 直接操作ではなく **python-pptx** を使う。

> **なぜ XML 直接操作ではなく python-pptx か**: テンプレートの XML 構造にはスライド間の相互参照（sldIdLst、p14:sectionLst、presentation.xml.rels）が多数含まれる。XML 直接操作でスライドを削除すると孤児参照が残り、PowerPoint が破損と判定する。python-pptx はこれらの参照を内部で管理するため、生 XML 操作より安全である。ただし、以下のスライド削除コードは `_sldIdLst` 等の private API に依存するため、python-pptx のバージョン更新時には動作確認が必要。

#### 手順

1. **テンプレートを .pptx に変換**: `.potx` を zip として開き、`[Content_Types].xml` 内の `presentationml.template.main+xml` を `presentationml.presentation.main+xml` に置換して `.pptx` として保存
2. **python-pptx で開く**: `Presentation('template.pptx')` でスライドマスター・レイアウトを含む状態で開く
3. **不要スライドを削除**: テンプレートのサンプルスライドを削除（下記コード参照）
4. **新規スライドを追加**: `prs.slide_layouts[N]` からレイアウトを選び、`prs.slides.add_slide(layout)` で追加
5. **コンテンツを設定**: プレースホルダにテキスト・表・画像を挿入
6. **保存**: `prs.save('output.pptx')`

#### python-pptx でのスライド削除

```python
def delete_slide(prs, slide_index):
    """指定インデックスのスライドを削除する。"""
    rId = prs.slides._sldIdLst[slide_index].get(
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    )
    prs.part.drop_rel(rId)
    del prs.slides._sldIdLst[slide_index]

# テンプレートスライドを末尾から削除（インデックスがずれないよう逆順）
for i in range(len(prs.slides) - 1, -1, -1):
    delete_slide(prs, i)
```

---

## Creating from Scratch

> 📌 **このリポジトリでは例外時のみ使用。** Azure template 利用が前提のため、ユーザーが明示的に例外を認めた場合のみ使う。

**Read [references/pptxgenjs.md](references/pptxgenjs.md) for full details.**

---

## 📌 スライドコンテンツのルール

### 言葉遣い
- 「ベストプラクティス」「自動」などの曖昧・冗長な表現を避け、具体的に何をどうするかを書く
- AIエージェントの動作として当然のこと（生成、取得、分析など）に「自動」は付けない
- 曖昧な用語は具体的な対象に置き換える（例: 「ベストプラクティス」→「Bicepスキーマ」「サービス推奨構成」）

### ツール・機能の出所を明記する
> 📌 Copilot CLI / MCP ツール紹介スライドを作る場合のルール。一般的なアーキテクチャ資料や業務資料には機械的に適用しない。

- ツールや機能をスライドで説明する際は、提供元を必ず明記する
  - Azure MCP Server のツール（aks, bicepschema, applens 等）
  - MS Learn MCP Server のツール（microsoft_docs_search, code_sample_search 等）
  - Copilot CLI 組み込み機能（/research, /model, /skills 等）
  - Copilot CLI Skill（azure-pptx, azure-drawio 等）
- グループヘッダ（太字）＋インデントされたサブ項目で構造化する
- ツール名だけ列挙せず、何ができるかを添える（例: 「applens」→「applens（「問題の診断と解決」機能）で問題を検出」）

### 聴衆視点での検証
- スライドを書く際は「聴衆がこれを見て理解できるか？次に何を知りたいか？」を考慮する
- 抽象的な説明には具体例（ツール名、コマンド例、ユースケース）を添える
- 専門用語やサービス名が初出の場合は、何であるかを補足する

### スライド構成・順序
- 同じカテゴリ・テーマのスライドは隣接させる
- スライドの追加・移動後は、孤立したスライドがないか全体を確認する
- 前のスライドで言及した概念が、後のスライドで説明される順序を意識する

---

## Design Ideas

> 📌 **テンプレート利用時の注意**: Azure template はブランドカラー（Azure Blue 系）・フォント（Segoe UI）が固定されている。以下の Color Palettes / Typography セクションはテンプレート未使用時（pptxgenjs）の参考であり、**Azure template 利用時はテンプレートのスタイルに従うこと**。レイアウト指針・スペーシング・Data display の考え方は参考にしてよい。

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders. Carry it across every slide.

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**Choose an interesting font pairing** — don't default to Arial. Pick a header font with personality and pair it with a clean body font.

| Header Font | Body Font |
|-------------|-----------|
| Georgia | Calibri |
| Arial Black | Arial |
| Calibri | Calibri Light |
| Cambria | Calibri |
| Trebuchet MS | Calibri |
| Impact | Arial |
| Palatino | Garamond |
| Consolas | Calibri |

| Element | Size |
|---------|------|
| Slide title | 36-44pt bold |
| Section header | 20-24pt bold |
| Body text | 14-16pt |
| Captions | 10-12pt muted |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```bash
uv run python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
uv run python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Visual QA

**⚠️ USE SUBAGENTS** — even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues — find them.

Look for:
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

---

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
uv run scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## Dependencies

> 📌 **このリポジトリでは `pip` を直接使わない。** `uv add`（プロジェクト依存）/ `uv pip install`（グローバル）/ PEP 723 インラインメタデータ（単一ファイルスクリプト）で管理すること。以下は必要なパッケージの一覧であり、インストールコマンドはリポジトリの規約に従う。

- `markitdown[pptx]` — text extraction（xlsx 読み取りには追加で `openpyxl` が必要）
- `Pillow` — thumbnail grids
- `defusedxml` — XML parsing（office scripts 全般で使用）
- `lxml` — XML validation and schema checking（validators で使用）
- `pptxgenjs`（npm） — creating from scratch
- LibreOffice (`soffice`) — PDF conversion (via `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) — PDF to image conversion
