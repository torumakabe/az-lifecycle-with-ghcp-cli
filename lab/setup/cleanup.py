# /// script
# requires-python = ">=3.10"
# ///
"""ラボ環境のクリーンアップスクリプト

Azure リソースの削除とリポジトリ生成物の除去を行い、
ラボをクリーンスタートできる状態に戻す。

Usage:
    uv run lab/setup/cleanup.py          # 確認プロンプト付き
    uv run lab/setup/cleanup.py --yes    # 確認なし（CI/自動化用）
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def confirm(message: str) -> bool:
    """ユーザーに確認を求める。y/Y で True を返す。"""
    answer = input(f"{message} [y/N]: ").strip()
    return answer.lower() in ("y", "yes")


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check)


def main() -> None:
    parser = argparse.ArgumentParser(description="ラボ環境クリーンアップ")
    parser.add_argument(
        "--yes", "-y", action="store_true", help="確認プロンプトをスキップ"
    )
    args = parser.parse_args()
    auto_yes: bool = args.yes

    if not (REPO_ROOT / ".git").is_dir():
        print("Error: リポジトリルートが見つかりません。", file=sys.stderr)
        sys.exit(1)

    # ============================================================================
    # Phase 1: Azure リソース削除
    # ============================================================================

    print("=== ラボ環境クリーンアップ ===")
    print()

    if shutil.which("azd"):
        print("[Phase 1] Azure リソース削除")
        if auto_yes or confirm("  azd down --force --purge を実行しますか？"):
            print("  Azure リソースを削除中...")
            result = run(["azd", "down", "--force", "--purge"], check=False)
            if result.returncode == 0:
                print("  Azure リソース削除完了")
            else:
                print(
                    "  Warning: azd down が失敗しました。環境が存在しない可能性があります。"
                )
        else:
            print("  スキップしました")
    else:
        print("[Phase 1] azd が見つかりません。Azure リソース削除をスキップします。")

    print()

    # ============================================================================
    # Phase 2: リポジトリ生成物削除
    # ============================================================================

    print("[Phase 2] リポジトリ生成物削除")

    if not auto_yes and not confirm("  ラボで生成されたファイルを削除しますか？"):
        print("  スキップしました")
        print()
        print("=== クリーンアップ完了 ===")
        return

    print()

    # ステージング解除 → 未追跡ファイル削除 → 追跡ファイル復元の順で実行。
    # git checkout -- . は staged な変更をリセットしないため、先にアンステージが必要。
    # ラボの成果物はすべて「追跡外」か「追跡ファイルへの変更」のいずれか。

    print("  ステージングを解除...")
    run(["git", "restore", "--staged", "."], check=True)
    print()

    print("  未追跡ファイル・.gitignore 対象を削除...")
    run(["git", "clean", "-fdx"], check=True)
    print()

    print("  追跡ファイルを初期状態に復元...")
    run(["git", "checkout", "--", "."], check=True)
    print()

    # ============================================================================
    # 結果レポート
    # ============================================================================

    print("=== クリーンアップ完了 ===")
    print()
    print("  次のステップ:")
    print("    1. git status で状態を確認")
    print("    2. lab/setup/README.md の手順に従ってラボ環境をセットアップ")


if __name__ == "__main__":
    main()
