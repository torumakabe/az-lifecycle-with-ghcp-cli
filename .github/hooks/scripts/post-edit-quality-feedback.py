# /// script
# requires-python = ">=3.10"
# ///
"""postToolUse hook: run edit-time quality checks and report feedback.

Runs after edit/create tool use:
  *.py    -> ruff check --fix + ruff format
  *.bicep -> az bicep format + az bicep build

When checks modify files or fail, emits additionalContext JSON for Copilot.
"""

import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from shutil import which

COMMAND_TIMEOUT_SEC = 20
MAX_OUTPUT_CHARS = 1600
MAX_CONTEXT_CHARS = 4000


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def failed(self) -> bool:
        return self.timed_out or self.returncode is None or self.returncode != 0


def to_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def resolve_command(command: list[str]) -> list[str]:
    executable = command[0]
    if Path(executable).name != executable:
        return command

    candidates = [executable]
    if os.name == "nt" and not Path(executable).suffix:
        candidates = [
            f"{executable}.exe",
            f"{executable}.cmd",
            f"{executable}.bat",
            executable,
        ]

    for candidate in candidates:
        resolved = which(candidate)
        if resolved:
            return [resolved, *command[1:]]

    return command


def run_command(
    command: list[str],
    *,
    timeout_sec: int = COMMAND_TIMEOUT_SEC,
    capture_stdout: bool = True,
) -> CommandResult:
    resolved_command = resolve_command(command)
    try:
        completed = subprocess.run(
            resolved_command,
            stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
    except FileNotFoundError:
        return CommandResult(
            command=command,
            returncode=None,
            stdout="",
            stderr=f"Command not found: {command[0]}",
        )
    except OSError as exc:
        return CommandResult(
            command=command,
            returncode=None,
            stdout="",
            stderr=f"Could not start command {command[0]}: {exc}",
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command=command,
            returncode=None,
            stdout=to_text(exc.stdout),
            stderr=to_text(exc.stderr),
            timed_out=True,
        )

    return CommandResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def summarize_output(result: CommandResult) -> str:
    output = "\n".join(part for part in (result.stderr, result.stdout) if part.strip())
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    summary = "\n".join(lines)
    if not summary:
        return "No output captured."
    if len(summary) <= MAX_OUTPUT_CHARS:
        return summary
    return f"{summary[:MAX_OUTPUT_CHARS].rstrip()}..."


def command_label(command: list[str]) -> str:
    if os.name != "nt":
        return shlex.join(command)
    return subprocess.list2cmdline(command)


def failure_message(path: Path, result: CommandResult) -> str:
    if result.timed_out:
        status = f"timed out after {COMMAND_TIMEOUT_SEC}s"
    elif result.returncode is None:
        status = "could not start"
    else:
        status = f"exited with code {result.returncode}"

    return (
        f"`{command_label(result.command)}` for `{path}` {status}. "
        f"Output summary: {summarize_output(result)}"
    )


def read_tool_args(raw_args: object) -> dict[str, object] | None:
    if isinstance(raw_args, str):
        try:
            parsed_args = json.loads(raw_args)
        except json.JSONDecodeError:
            return None
    else:
        parsed_args = raw_args

    if not isinstance(parsed_args, dict):
        return None
    return parsed_args


def additional_context(messages: list[str]) -> str:
    context = "postToolUse quality hook feedback:\n" + "\n".join(
        f"- {message}" for message in messages
    )
    if len(context) <= MAX_CONTEXT_CHARS:
        return context
    return f"{context[:MAX_CONTEXT_CHARS].rstrip()}..."


def emit_additional_context(messages: list[str]) -> None:
    if not messages:
        return
    json.dump({"additionalContext": additional_context(messages)}, sys.stdout)


def file_changed_message(path: Path) -> str:
    return (
        f"Quality hook modified `{path}`. Re-read the file before making "
        "further edits so subsequent changes use the latest content."
    )


def process_python(path: Path) -> list[str]:
    before = path.read_bytes()
    messages: list[str] = []

    for command in (
        ["uvx", "ruff", "check", "--fix", "--quiet", str(path)],
        ["uvx", "ruff", "format", "--quiet", str(path)],
    ):
        result = run_command(command)
        if result.failed:
            messages.append(failure_message(path, result))

    if path.exists() and path.read_bytes() != before:
        messages.append(file_changed_message(path))

    return messages


def process_bicep(path: Path) -> list[str]:
    before = path.read_bytes()
    messages: list[str] = []

    format_result = run_command(["az", "bicep", "format", "--file", str(path)])
    if format_result.failed:
        messages.append(failure_message(path, format_result))
    else:
        build_result = run_command(
            ["az", "bicep", "build", "--file", str(path), "--stdout"],
            capture_stdout=False,
        )
        if build_result.failed:
            messages.append(failure_message(path, build_result))

    if path.exists() and path.read_bytes() != before:
        messages.append(file_changed_message(path))

    return messages


def target_path(data: dict[str, object]) -> Path | None:
    raw_args = data.get("toolArgs", data.get("tool_input", {}))
    tool_args = read_tool_args(raw_args)
    if tool_args is None:
        return None

    file_path = tool_args.get("path") or tool_args.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return None
    return Path(file_path)


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return

    tool_name = str(data.get("toolName", data.get("tool_name", ""))).lower()
    if tool_name not in ("edit", "create", "write"):
        return

    path = target_path(data)
    if path is None:
        return

    suffix = path.suffix.lower()
    if not path.exists():
        return

    messages: list[str] = []
    if suffix == ".py":
        messages = process_python(path)
    elif suffix == ".bicep":
        messages = process_bicep(path)

    emit_additional_context(messages)


if __name__ == "__main__":
    main()
