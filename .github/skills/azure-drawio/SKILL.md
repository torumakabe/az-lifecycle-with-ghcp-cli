---
name: azure-drawio
description: "Generate Azure architecture diagrams as editable .drawio files with official Azure icons. Outputs native draw.io XML (mxGraphModel format) that can be opened and edited in draw.io Desktop, VS Code draw.io extension, or draw.io Web."
license: Apache-2.0 (derived from jgraph/drawio-mcp). See LICENSE.txt
---

# Azure Draw.io Diagram Skill

> **出自**: [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp) をベースに、このリポジトリ向けの運用ルールを追加。  
> 「📌」マークのあるセクションは本リポジトリ専用のルールであり、アップストリームには含まれない。

Azure アーキテクチャ構成図を draw.io XML（mxGraphModel 形式）で生成するスキル。
draw.io 組み込みの Azure 公式アイコン（`img/lib/azure2/`）を使用し、`.drawio` ファイルとして出力する。

## 構成図の作り方

1. ユーザーの要求に基づき、Azure サービスの構成図を設計する
2. draw.io XML（mxGraphModel 形式）を生成する
3. `.drawio` ファイルとして保存する
4. ファイルを開く

## 📌 PowerPoint / PPTX 向けの図の作り方

`azure-pptx` Skill や `docs/overview.pptx` のようなスライド資料に載せる図は、**「draw.io 上で正しい図」ではなく「1 スライドで読める図」** として設計する。

### まず図の役割を決める

- 1ページ = 1メッセージに絞る
- 全体構成、PoC 接続、本番閉域化、コスト関連など、説明の観点が異なるものは別ページに分ける
- 「全体図」と「通信経路の詳細」を同じページに押し込まない

### 分割を先に決める

次のいずれかに当てはまる場合は、**PowerPoint へ貼る前提では 1 枚に収めず複数ページへ分割**する。

1. 主要リソースが 8 個を超える
2. コンテナ階層が 3 段を超える
3. 接続線が 6 本を超える
4. ページ内で「全体の所属関係」と「個別の通信経路詳細」を同時に説明している

### 可読性のルール

- 主要ラベルは 2 行以内に収める
- リソース名に環境名や長いサフィックスが含まれる場合、図中は要約名にし、詳細名は別テキストや脚注へ逃がす
- 小さく縮小されても読めるよう、**最小文字サイズありきで詰め込まない**
- アイコン数を減らせない場合は、アイコンを小さくするのではなくページを分ける

### 推奨するページ構成

- **ページ 1: 全体構成** — 外部、Resource Group、VNet、主要 PaaS の所属関係を示す
- **ページ 2: PoC / 開発系** — Public access、firewallRules、開発者アクセス経路に絞る
- **ページ 3: 本番 / 閉域系** — Private Endpoint、Private DNS、VNet Integration に絞る

### `azure-pptx` と組み合わせるときの前提

- PowerPoint 側で 1 枚の大きな図をトリミングして使う前提にしない
- draw.io 側で **スライド単位にページ分割した PNG / SVG** を出す
- スライドに載せる画像は「図全体を読む」ためではなく、「要点を補強する視覚要素」として扱う

## XML 基本構造

すべての `.drawio` ファイルは以下の構造を持つ:

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0" adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
  </root>
</mxGraphModel>
```

- `id="0"` はルートレイヤー（必須）
- `id="1"` はデフォルト親レイヤー（必須）
- すべての図形は `parent="1"` を指定（グループ内は親のIDを指定）
- `adaptiveColors="auto"` でダークモード時の色自動適応を有効化

### 📌 PowerPoint 用キャンバス

アップストリームの基本構造はそのままでよいが、**PowerPoint に載せる用途では横長の 16:9 前提でレイアウト**する。重要なのは XML の数値そのものより、次の運用ルール。

- 左右に余白を残し、端まで要素を寄せない
- 横方向に 2〜3 列の情報配置で完結する密度に抑える
- 下端に長いラベルや注釈が落ちる構図を避ける
- 1ページ内で「凡例」「詳細注記」「通信経路」を全部載せない

## Azure アイコンの使い方

### style の共通形式

Azure アイコンは以下の style を使用する:

```
image;aspect=fixed;html=1;points=[];align=center;fontSize=12;image=img/lib/azure2/{カテゴリ}/{SVGファイル名};
```

### アイコンセルの記述例

```xml
<mxCell id="2" value="App Service" style="image;aspect=fixed;html=1;points=[];align=center;fontSize=12;image=img/lib/azure2/app_services/App_Services.svg;" vertex="1" parent="1">
  <mxGeometry x="200" y="150" width="64" height="64" as="geometry"/>
</mxCell>
```

- `value`: ラベルテキスト（アイコンの下に表示される）
- `width` / `height`: アイコンサイズ（推奨: 48〜68）
- `aspect=fixed`: アスペクト比を固定（必須）

## グルーピング（コンテナ）

### コンテナの仕組み

子セルに `parent="コンテナID"` を設定する。子は**コンテナ内の相対座標**を使用する。

### コンテナの種類

| 種類 | style | 用途 |
|------|-------|------|
| **Group**（不可視） | `group;` | 枠線不要、コンテナ自体に接続線がない場合。`pointerEvents=0` を含むため子の接続を奪わない |
| **Swimlane**（タイトル付き） | `swimlane;startSize=30;` | ヘッダー/タイトルバーが必要、またはコンテナ自体に接続線がある場合 |
| **カスタムコンテナ** | 任意の shape に `container=1;pointerEvents=0;` を追加 | 任意の図形をコンテナ化（接続線を持たない場合） |

### 重要なルール

- コンテナ自体が接続線を持たない場合、**`pointerEvents=0;`** を style に追加する（子の接続をコンテナが奪うのを防ぐ）
- コンテナ自体が接続可能である必要がある場合は `swimlane` を使う（ヘッダー部分が接続可能、クライアント領域はマウスイベントを透過）
- 子セルは `parent="コンテナID"` を設定し、**コンテナ内の相対座標**を使用する

### Azure コンテナの style 例

```xml
<mxCell id="10" value="Resource Group" style="rounded=1;whiteSpace=wrap;fillColor=none;strokeColor=#0078D4;dashed=1;verticalAlign=top;fontStyle=1;fontSize=14;fontColor=#0078D4;arcSize=5;container=1;pointerEvents=0;" vertex="1" parent="1">
  <mxGeometry x="50" y="50" width="600" height="400" as="geometry"/>
</mxCell>

<mxCell id="11" value="Virtual Network" style="rounded=1;whiteSpace=wrap;fillColor=none;strokeColor=#3B3B3B;dashed=1;dashPattern=5 5;verticalAlign=top;fontStyle=1;fontSize=13;fontColor=#3B3B3B;arcSize=5;container=1;pointerEvents=0;" vertex="1" parent="10">
  <mxGeometry x="30" y="40" width="540" height="340" as="geometry"/>
</mxCell>

<mxCell id="12" value="App Service" style="image;aspect=fixed;html=1;points=[];align=center;fontSize=12;image=img/lib/azure2/app_services/App_Services.svg;" vertex="1" parent="11">
  <mxGeometry x="20" y="40" width="64" height="64" as="geometry"/>
</mxCell>
```

### Swimlane の例

```xml
<mxCell id="svc1" value="User Service" style="swimlane;startSize=30;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="300" height="200" as="geometry"/>
</mxCell>
<mxCell id="api1" value="REST API" style="rounded=1;whiteSpace=wrap;" vertex="1" parent="svc1">
  <mxGeometry x="20" y="40" width="120" height="60" as="geometry"/>
</mxCell>
```

## レイアウトのベストプラクティス

Azure Well-Architected Framework のダイアグラムガイドライン（[Design diagrams](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/design-diagrams)）に基づく。

### 所属関係と通信フローを区別する

- **所属関係**（リソースがVNet/サブネット/リソースグループに属する）→ **枠内に配置**して表現する
- **通信フロー**（リソース間のデータの流れ、リクエスト/レスポンス）→ **矢印（エッジ）** で表現する
- 所属関係を矢印で表現しない。読み手が通信フローと混同する

### 正確に描く

- PaaS サービスがサブネット内にデプロイされていない場合は、サブネット枠外に配置する
- Private Endpoint 経由でアクセスする場合は、エンドポイントをサブネット内に配置し、PaaS 本体は枠外に描く
- VM やその他 IaaS リソースがサブネットにデプロイされている場合は、サブネット枠内に配置する
- 不正確な簡略化は誤解や実装エラーの原因になる

### 矢印のルール

- 矢印なしの線は使わない。常に方向付き矢印を使う
- 起点（クライアント/呼び出し元）→ 終点（サーバー/依存先）の向きで描く
- 双方向矢印は避ける。必要なら単方向矢印を2本使うか、注釈で補足する
- **矢印は確認された事実のみ表現する**。IaC（Bicep/Terraform）から読み取れるのはリソース定義とセキュリティルールであり、実際のアプリケーション通信フローではない。NSGの許可ルールがあるだけでは通信フローの矢印を引かない。矢印を引く場合はアプリケーション設計やコードで通信が確認できる場合に限る

### ラベルと一貫性

- すべてのアイコン、グループ枠、接続線にラベルを付ける
- 色、アイコンサイズ、線の太さ、線種を統一する
- 公式アイコンと公式サービス名を使用する

### 📌 スライド投影を前提にしたラベル短縮

スライド用途では、正式名称を毎回フルで書くよりも、**投影時に読める短さ**を優先する。

- `Azure Database for PostgreSQL flexible server` → `PostgreSQL Flexible Server`
- `Azure Monitor Log Analytics Workspace` → `Log Analytics Workspace`
- `privatelink.postgres.database.azure.com` のような長い FQDN は、必要なら 2 行に分けるか別注記へ逃がす

正式名称が必要な場合は、図中ラベルではなく本文・脚注・別ページで補う。

### ラベルのはみ出しとコンテナマージン

Azure アイコンのラベル（`align=center`）はアイコンの下に中央揃えで描画される。ラベルのテキスト幅はアイコンの幅を大きく超えるため、コンテナの端にアイコンを配置するとラベルがコンテナ外にはみ出す。はみ出したラベルは PNG/SVG エクスポート時に切れる。

**ラベル幅の目安:**

| fontSize | ラベル例 | おおよそのテキスト幅 |
|----------|---------|-------------------|
| 10 | `PostgreSQL Flexible Server` (26文字) | ~140px |
| 11 | `Log Analytics Workspace` (24文字) | ~145px |
| 11 | `Private DNS Zone` + 改行 + `privatelink.postgres...` | ~155px |
| 12 | `App Service Plan` (16文字) | ~115px |

ラベルは中央揃えのため、アイコン中心から左右に `テキスト幅 / 2` だけ拡がる。複数行ラベル（`&#xa;` で改行）は最も長い行の幅が使われる。

**ルール:**

1. **コンテナ端からアイコン中心までの距離 ≥ 最長ラベル行の半幅 + 20px（余裕）** を確保する
2. 実用的な目安: fontSize 10〜12 の一般的な Azure サービス名であれば、**コンテナ端からアイコン中心まで最低 100px** を確保する
3. コンテナの右端・下端は特に注意する（ページ境界と重なりやすい）
4. コンテナ幅が足りなければ、アイコンを寄せるのではなくコンテナを広げる

**悪い例:**

```xml
<mxCell id="10" style="...container=1..." vertex="1" parent="1">
  <mxGeometry x="130" y="20" width="1010" height="780" as="geometry"/>
</mxCell>
<mxCell id="21" value="Log Analytics Workspace&#xa;log-myproj-{env}" style="...fontSize=11;..." vertex="1" parent="10">
  <mxGeometry x="870" y="60" width="50" height="50" as="geometry"/>
</mxCell>
```

**良い例:**

```xml
<mxCell id="21" value="Log Analytics Workspace&#xa;log-myproj-{env}" style="...fontSize=11;..." vertex="1" parent="10">
  <mxGeometry x="790" y="60" width="50" height="50" as="geometry"/>
</mxCell>
```

## 接続線（エッジ）

基本の矢印:

```xml
<mxCell id="100" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#0078D4;" edge="1" source="2" target="3" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

ラベル付き矢印:

```xml
<mxCell id="101" value="HTTPS" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#0078D4;fontSize=11;" edge="1" source="2" target="3" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

破線の矢印（オプショナルな接続）:

```xml
<mxCell id="102" style="edgeStyle=orthogonalEdgeStyle;dashed=1;strokeColor=#999999;" edge="1" source="2" target="3" parent="1">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

### エッジルーティング

**重要: すべての edge mxCell には `<mxGeometry relative="1" as="geometry"/>` 子要素が必須。** 自己閉じタグ（`<mxCell ... edge="1" ... />`）は無効でレンダリングされない。常に展開形式を使う:

```xml
<mxCell id="e1" edge="1" parent="1" source="a" target="b" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#0078D4;">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

draw.io にはエッジの衝突検出がない。レイアウトとルーティングを慎重に計画すること:

- `edgeStyle=orthogonalEdgeStyle` で直角コネクタを使用する（最も一般的）
- **ノード間隔を十分に取る** — 最低60px、推奨は横200px / 縦120px
- `exitX`/`exitY` と `entryX`/`entryY`（値 0〜1）でエッジの接続位置を制御する。複数の接続は異なる辺に分散させ、重なりを防ぐ
- **矢印の余白を確保する**: エッジの最終直線セグメント（最後の曲がりからターゲットまで）は矢印が収まる長さが必要。ターゲット手前・ソース直後に最低20pxの直線セグメントを確保する
- `orthogonalEdgeStyle` の自動ルーターは自動で曲がりを配置するが、ノードが近すぎると矢印が曲がり部分に重なる。ノード間隔を広げるか、明示的なウェイポイントで回避する
- エッジが重なる場合は明示的な**ウェイポイント**を追加する:
  ```xml
  <mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#0078D4;" edge="1" parent="1" source="a" target="b">
    <mxGeometry relative="1" as="geometry">
      <Array as="points">
        <mxPoint x="300" y="150"/>
        <mxPoint x="300" y="250"/>
      </Array>
    </mxGeometry>
  </mxCell>
  ```
- `rounded=1` でエッジの曲がりを滑らかにする
- `jettySize=auto` で orthogonal エッジのポート間隔を改善する
- すべてのノードをグリッドに合わせる（10の倍数）
- **エッジラベルに HTML マークアップを使わない**。エッジラベルのデフォルト font size は 11px（頂点の 12px より小さい）。`<font size="2">` 等で縮小する必要はなく、`value` 属性にテキストを直接設定する

## XML の注意事項

- XML コメント（`<!-- -->`）は**一切生成しないこと**。トークンの浪費になり、パースエラーの原因にもなる。ダイアグラム XML にコメントは不要
- 属性値内の特殊文字はエスケープする: `&amp;`, `&lt;`, `&gt;`, `&quot;`
- すべての `mxCell` に一意の `id` を付与する
- アイコンセルには `vertex="1"` を、接続線には `edge="1"` を指定する
- **edge の mxCell を自己閉じタグにしない**。`<mxGeometry relative="1" as="geometry"/>` 子要素が必須

## レイヤー

レイヤーは表示/非表示を切り替えられるグループ単位。z-order の制御にも使える。Azure 構成図では「物理インフラ」「論理ネットワーク」「注釈」等を分離すると、閲覧者が必要な情報だけを表示できる。

`id="0"` はルート、`id="1"` はデフォルトレイヤー（常に存在）。追加レイヤーは `parent="0"` を持つ `mxCell`（`vertex` / `edge` 属性なし）として定義する:

```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="2" value="Annotations" parent="0"/>
    <mxCell id="10" value="App Service" style="image;aspect=fixed;html=1;points=[];align=center;fontSize=12;image=img/lib/azure2/app_services/App_Services.svg;" vertex="1" parent="1">
      <mxGeometry x="100" y="100" width="64" height="64" as="geometry"/>
    </mxCell>
    <mxCell id="20" value="Note: deprecated" style="text;" vertex="1" parent="2">
      <mxGeometry x="100" y="170" width="120" height="30" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>
```

- 後に定義したレイヤーが上に描画される（z-order が高い）
- `visible="0"` をレイヤーセルに追加するとデフォルト非表示になる
- 図形をレイヤーに所属させるには `parent` にレイヤーの id を指定する
- レイヤーは表示フィルタであり、コンテナ（グルーピング）とは異なる。構造的な入れ子にはコンテナを使う

## ダークモード色

draw.io はダークモードレンダリングをサポートしている。色の挙動:

- **明示的な色を指定しない場合**: `strokeColor`, `fillColor`, `fontColor` はデフォルト値 `"default"` となり、ライトテーマでは黒、ダークテーマでは白として自動適応する
- **明示的に色を指定した場合**（例: `fillColor=#DAE8FC`）: 指定した色はライトモードの色として扱われ、ダークモードでは RGB 反転（93% ブレンド）+ 色相 180° 回転で自動計算される
- **両モードの色を個別指定する場合**: `light-dark(lightColor,darkColor)` 関数を使う（例: `fontColor=light-dark(#7EA6E0,#FF0000)`）

ダークモード色適応を有効化するには `<mxGraphModel>` に `adaptiveColors="auto"` が必要（基本構造テンプレート参照）。

Azure 構成図で `strokeColor=#0078D4`（Azure Blue）等を明示指定した場合、ダークモードでは自動反転された色が使われる。多くの場合、自動反転で十分な視認性が得られるため、`light-dark()` による個別指定は必要ない。自動反転色が不適切な場合のみ `light-dark()` を使用する。

## スタイルリファレンス

- draw.io スタイルリファレンス: https://github.com/jgraph/drawio-mcp/blob/main/shared/style-reference.md
- XML Schema Definition (XSD): https://github.com/jgraph/drawio-mcp/blob/main/shared/mxfile.xsd

## エクスポート（PNG/SVG/PDF）

draw.io デスクトップアプリの CLI でエクスポートできる。`--embed-diagram` を使うとエクスポート先ファイルに XML が埋め込まれ、draw.io で再編集可能。

### CLI の場所

`drawio` がパスにない場合、プラットフォーム別のパスを使う:

- **macOS**: `/Applications/draw.io.app/Contents/MacOS/draw.io`
- **Linux**: `drawio`（snap/apt/flatpak でインストール済みの場合）
- **Windows**: `"C:\Program Files\draw.io\draw.io.exe"`
- **WSL2**: `` `/mnt/c/Program Files/draw.io/draw.io.exe` ``（WSL2 検出: `grep -qi microsoft /proc/version 2>/dev/null`）

### エクスポートコマンド

```bash
drawio -x -f <format> -e -b 10 -o <output> <input.drawio>
```

主要フラグ:
- `-x` / `--export`: エクスポートモード
- `-f` / `--format`: 出力形式（png, svg, pdf, jpg）
- `-e` / `--embed-diagram`: 出力に XML を埋め込む（PNG, SVG, PDF のみ）
- `-o` / `--output`: 出力ファイルパス
- `-b` / `--border`: 図の周囲の余白（デフォルト: 0）

> 📌 **`--border` は 80 以上を推奨。** Azure アイコンのラベルはアイコン幅を大きく超えるため、小さい値ではラベルが端で切れる。PPTX やドキュメントに埋め込む場合は特に注意。

### 📌 PowerPoint 用エクスポート運用

PowerPoint に貼る場合は、**1 つの巨大なページをあとから切り出す運用より、draw.io のページを分けて個別エクスポートする運用を優先**する。

- 1ページごとに PNG / SVG を出力する
- overview / poc / production など、スライドの区切りに合わせてページを分ける
- 1枚の PNG を PowerPoint 側で拡大・トリミングして読ませる前提にしない
- スクリーンショット用途では PNG、再編集前提なら SVG も併用する

PowerPoint 連携時の推奨フロー:

1. draw.io でスライド単位にページ分割する
2. 各ページを `-b 80` 以上で個別エクスポートする
3. `azure-pptx` 側では、画像をそのまま載せるか、要約テキストと併置する

| 形式 | XML 埋め込み | 備考 |
|------|-------------|------|
| `png` | 対応 (`-e`) | どこでも表示可能、draw.io で編集可能 |
| `svg` | 対応 (`-e`) | スケーラブル、draw.io で編集可能 |
| `pdf` | 対応 (`-e`) | 印刷向き、draw.io で編集可能 |
| `jpg` | 非対応 | 非可逆、XML 埋め込み不可 |

### ファイルを開く

- **macOS**: `open <file>`
- **Linux**: `xdg-open <file>`
- **Windows**: `start <file>`
- **WSL2**: `cmd.exe /c start "" "$(wslpath -w <file>)"`（`wslpath -w` で WSL パスを Windows パスに変換。`start` 直後の `""` はウィンドウタイトル用の空文字で必須）

## ファイル命名規則

- `<説明的な名前>.drawio`（例: `web-app-architecture.drawio`）
- エクスポート時はダブル拡張子: `name.drawio.png`, `name.drawio.svg`, `name.drawio.pdf`（XML 埋め込み済みであることを示す）
- 小文字・ハイフン区切り

## 完全なサンプル: App Service + Cosmos DB + Front Door

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0" adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="10" value="Resource Group: rg-webapp" style="rounded=1;whiteSpace=wrap;fillColor=none;strokeColor=#0078D4;dashed=1;verticalAlign=top;fontStyle=1;fontSize=14;fontColor=#0078D4;arcSize=5;" vertex="1" parent="1">
      <mxGeometry x="120" y="40" width="920" height="420" as="geometry"/>
    </mxCell>
    <mxCell id="2" value="Users" style="image;aspect=fixed;html=1;points=[];align=center;fontSize=12;image=img/lib/azure2/identity/Users.svg;" vertex="1" parent="1">
      <mxGeometry x="30" y="210" width="52" height="57" as="geometry"/>
    </mxCell>
    <mxCell id="3" value="Front Door" style="image;aspect=fixed;html=1;points=[];align=center;fontSize=12;image=img/lib/azure2/networking/Front_Doors.svg;" vertex="1" parent="1">
      <mxGeometry x="200" y="210" width="65" height="57" as="geometry"/>
    </mxCell>
    <mxCell id="4" value="App Service" style="image;aspect=fixed;html=1;points=[];align=center;fontSize=12;image=img/lib/azure2/app_services/App_Services.svg;" vertex="1" parent="1">
      <mxGeometry x="460" y="210" width="64" height="64" as="geometry"/>
    </mxCell>
    <mxCell id="5" value="Cosmos DB" style="image;aspect=fixed;html=1;points=[];align=center;fontSize=12;image=img/lib/azure2/databases/Azure_Cosmos_DB.svg;" vertex="1" parent="1">
      <mxGeometry x="740" y="120" width="64" height="64" as="geometry"/>
    </mxCell>
    <mxCell id="6" value="App Service Plan" style="image;aspect=fixed;html=1;points=[];align=center;fontSize=12;image=img/lib/azure2/app_services/App_Service_Plans.svg;" vertex="1" parent="1">
      <mxGeometry x="460" y="340" width="64" height="64" as="geometry"/>
    </mxCell>
    <mxCell id="7" value="Application&#xa;Insights" style="image;aspect=fixed;html=1;points=[];align=center;fontSize=12;image=img/lib/azure2/devops/Application_Insights.svg;" vertex="1" parent="1">
      <mxGeometry x="740" y="300" width="44" height="63" as="geometry"/>
    </mxCell>
    <mxCell id="20" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#0078D4;" edge="1" source="2" target="3" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="21" value="HTTPS" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#0078D4;fontSize=11;" edge="1" source="3" target="4" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="22" style="edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#0078D4;" edge="1" source="4" target="5" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="23" style="edgeStyle=orthogonalEdgeStyle;dashed=1;strokeColor=#999999;" edge="1" source="4" target="7" parent="1">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>
```


## Azure アイコン一覧

詳細は [references/azure-icons.md](references/azure-icons.md) を参照。
style の `image=img/lib/azure2/{カテゴリ}/{SVGファイル名}` に指定する。
