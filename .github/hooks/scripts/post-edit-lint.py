# /// script
# requires-python = ">=3.10"
# ///
"""postToolUse hook: auto-lint/format after file edits.

Runs silently after edit/create tool use:
  *.py    -> ruff check --fix + ruff format
  *.bicep -> az bicep format
"""

import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    tool_name = data.get("toolName", "")
    if tool_name not in ("edit", "create"):
        return

    # toolArgs may be a JSON string (per docs) or already-parsed dict
    raw_args = data.get("toolArgs", {})
    if isinstance(raw_args, str):
        try:
            tool_args = json.loads(raw_args)
        except json.JSONDecodeError:
            return
    else:
        tool_args = raw_args

    file_path = tool_args.get("path") or tool_args.get("file_path", "")
    if not file_path:
        return

    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".py" and path.exists():
        subprocess.run(
            ["uvx", "ruff", "check", "--fix", "--quiet", str(path)],
            capture_output=True,
        )
        subprocess.run(
            ["uvx", "ruff", "format", "--quiet", str(path)],
            capture_output=True,
        )

    elif suffix == ".bicep" and path.exists():
        subprocess.run(
            ["az", "bicep", "format", "--file", str(path)],
            capture_output=True,
        )


if __name__ == "__main__":
    main()
