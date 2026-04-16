---
name: bicep-api-version-updater
description: BicepファイルのAzure リソースAPIバージョンを最新化。「APIバージョンを更新」「Bicepを最新化」「古いAPIバージョンをチェック」を求める場合に使用。
---

# Bicep API Version Updater

BicepファイルのAzureリソースAPIバージョンを最新の安定版に更新する。

## Tools

| Tool | 用途 |
|------|------|
| `az provider show` | 最新GA版の取得（プライマリ） |
| `microsoft_docs_fetch` | 最新GA版の取得（フォールバック：APIリファレンス参照） |
| `az bicep build` | 構文検証・Linterチェック |
| `microsoft_docs_search` | Breaking changes情報の検索 |
| `grep` / `view` | Bicepファイルの解析 |
| `edit` | APIバージョンの更新 |

### bicepschemaを使用しない理由

Azure MCP Serverの`bicepschema`と`az provider show`では、APIバージョンの取得元が異なる。

| ツール | データソース | 更新タイミング |
|--------|-------------|---------------|
| `bicepschema` | Bicep CLIに同梱された型定義（[Azure/bicep-types-az](https://github.com/Azure/bicep-types-az)） | Bicep CLIのリリース時 |
| `az provider show` | Azureリソースプロバイダーへのリアルタイム問い合わせ | 常に最新 |

この設計上の差異により、`bicepschema`が返す「最新版」がBicep CLIのバージョンに依存し、実際の最新GA版より古い場合がある。最新版の判定には`az provider show`を使用する。

> **参考:** `bicepschema`の最新版選択ロジックは[ApiVersionSelector.cs](https://github.com/microsoft/mcp/blob/main/tools/Azure.Mcp.Tools.BicepSchema/src/Services/Support/ApiVersionSelector.cs)で実装されており、安定版を優先してソート・選択する仕様となっている。

### az provider showの制限

`az provider show` はリソースプロバイダーに登録されているリソースタイプのみを返す。一部の子リソース（例: `redisEnterprise/databases/accessPolicyAssignments`）は登録されていない場合があり、その場合はAPIリファレンスを参照する必要がある。

## 更新フロー（概要）

更新フロー: Bicepファイル解析 → プレビュー版スキップ判定 → 最新GA版取得・比較 → Breaking Changes確認 → 仮適用 → Linter検証（警告時はロールバック）。各ステップの詳細は「実行手順」を参照。

## スキップ理由の分類

| 理由 | 報告時の状態 | 追加アクション |
|------|-------------|---------------|
| プレビュー版使用中 | ⏭️ スキップ（プレビュー版） | GA移行可否の分析（必須） |
| 既に最新GA版 | ⏭️ スキップ（既に最新） | なし |
| GA版が存在しない | ⏭️ スキップ（GA版なし） | なし |
| Linter警告発生 | ⚠️ スキップ（BCP081警告） | なし |

## 実行手順

### Step 1: リソースタイプとAPIバージョンの抽出

> **注意:** 以下のコマンド例は bash 前提。AI エージェントは `grep` ツールを使用すること。PowerShell 環境では対応するコマンドレットで代替すること。

```bash
grep -E "^resource\s+" infra/**/*.bicep
```

> **対象外:** `resourceInput<'Type@version'>` / `resourceOutput<'Type@version'>` 構文（Bicep 0.34.1以降）は本スキルの対象外。これらは型定義用でありリソースをデプロイしないため、APIバージョン更新の優先度が異なる。

### Step 2: プレビュー版のスキップ判定

APIバージョンに `-preview` が含まれる場合は**更新をスキップ**。

**理由:** プレビューAPIを使用しているリソースは、GA版では提供されない機能を意図的に利用しているケースが多い。機械的にGA版へ置き換えると、必要な機能が失われるリスクがある。

**ただし、以下の分析は必ず実施すること:**

1. 現在のBicepファイルで使用している属性を特定
2. `az provider show` で最新GA版を取得
3. コードの属性がGA版でサポートされているか確認（ドキュメント検索）
4. 結果を出力フォーマットの「プレビュー版分析セクション」に含める

### Step 3: 最新GA版の取得と比較

#### 3-1. 最新GA版の取得

> **注意:** 以下のコマンド例は bash 前提。AI エージェントは `az provider show` の結果を解析して同等の処理を行うこと。PowerShell 環境では対応するコマンドレットで代替すること。

```bash
az provider show -n Microsoft.Network \
  --query "resourceTypes[?resourceType=='virtualNetworks'].apiVersions" \
  -o tsv | tr '\t' '\n' | grep -iv preview | sort -r | head -1
```

> **注意:** `az provider show` の返すAPIバージョン一覧は降順ソートされているように見えるが、公式ドキュメントでは保証されていない。`sort -r` でクライアント側ソートを行い、確実に最新版を取得する。

複数リソースタイプの一括取得（bash 前提。AI エージェントはリソースタイプごとに `az provider show` を実行して同等の処理を行うこと）:
```bash
for provider_resource in \
  "Microsoft.ManagedIdentity:userAssignedIdentities" \
  "Microsoft.Network:virtualNetworks" \
  "Microsoft.Authorization:roleAssignments"
do
  provider="${provider_resource%%:*}"
  resource="${provider_resource##*:}"
  echo "=== $provider/$resource ==="
  az provider show -n "$provider" \
    --query "resourceTypes[?resourceType=='$resource'].apiVersions" \
    -o tsv 2>/dev/null | tr '\t' '\n' | grep -iv preview | sort -r | head -1
done
```

#### 3-2. 比較と判断

- 現在のバージョン == 最新GA版 → スキップ（既に最新）
- 現在のバージョン < 最新GA版 → Step 4へ

#### 3-3. フォールバック: APIリファレンス参照

`az provider show` で結果が空の場合（リソースタイプが登録されていない場合）、`microsoft_docs_fetch` でAPIリファレンスを参照:

```
URL形式:
https://learn.microsoft.com/en-us/azure/templates/{provider}/{resourceType}

例:
https://learn.microsoft.com/en-us/azure/templates/microsoft.cache/redisenterprise/databases/accesspolicyassignments
```

APIリファレンスページの上部に利用可能なAPIバージョン一覧が表示される。`-preview` を含まない最新バージョンを選択する。

### Step 4: Breaking Changes確認

`microsoft_docs_search` で破壊的変更を検索:

```
検索クエリ例:
- "Microsoft.ContainerService managedClusters API breaking changes"
```

参考リンク:
- AKS: https://aka.ms/aks/breakingchanges

### Step 5: APIバージョン更新（仮適用）

`edit` ツールで更新。この時点では「仮適用」。

### Step 6: Linter検証と更新確定

```bash
az bicep build --file infra/main.bicep 2>&1
```

#### 警告が出た場合の対応（必須）

1. **更新前のバージョンに戻す**
2. 「スキップされたリソース」として報告

**理由:** Bicep型定義が未対応の場合、プロパティの検証ができず意図しないデプロイエラーのリスクがある。Bicep CLIが更新されれば自動的に対応されるため、待つ方が安全。

**禁止:** 最新GA版でBCP081警告が出た場合に、警告が出ない別のバージョンへ変更すること。元のバージョンに戻すのみ許可。

**例外:** `#disable-next-line BCP081` で意図的に警告を抑制しているリソースは、更新を許可する（Linterが警告しない）。

#### 警告が出なかった場合

更新確定。

## 出力フォーマット（必須）

以下のセクションを**必ず**含めること:

1. **更新サマリーテーブル** - 全リソースの更新状況（BCP081警告も含む）
2. **プレビュー版分析セクション** - GA移行可否と理由（プレビュー版が存在する場合）

### テンプレート

```markdown
## APIバージョン更新サマリー

| ファイル | リソースタイプ | 更新前 | 更新後 | 状態 |
|----------|---------------|--------|--------|------|
| identity.bicep | Microsoft.ManagedIdentity/userAssignedIdentities | 2023-01-31 | 2024-11-30 | ✅ 更新 |
| aks.bicep | Microsoft.ContainerService/managedClusters | 2025-06-02-preview | - | ⏭️ スキップ（プレビュー版） |
| network.bicep | Microsoft.Network/virtualNetworks | 2024-07-01 | - | ⏭️ スキップ（既に最新） |
| network.bicep | Microsoft.Network/publicIPAddresses | 2024-07-01 | - | ⚠️ スキップ（BCP081警告） |

**BCP081警告について:** 最新GA版への更新を試みたが、Bicep型定義が未対応のため元のバージョンを維持した。Bicep CLI更新後に再実行で更新可能になる場合がある。

### スキップされたプレビュー版リソースの分析

| ファイル | リソースタイプ | 現在のバージョン | 最新GA版 | GA移行可否 |
|----------|---------------|-----------------|---------|-----------|
| aks.bicep | Microsoft.ContainerService/managedClusters | 2025-06-02-preview | 2025-10-01 | ❌ 不可 |

**GA版に存在しない属性:**
- `properties.networkProfile.advancedNetworking.security.advancedNetworkPolicies`

上記の属性はプレビュー専用のため、GA版への移行には機能の代替または削除が必要である。
すべての属性がGA版に存在する場合は「✅ 可能」と表示され、GA版への移行を検討できる。
```

## 前提条件

- Azure CLIでログイン済み（`az login`）
- Bicep CLIがインストール済み
