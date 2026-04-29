import os
import subprocess
import sys
import threading
from collections import deque
from typing import IO, TypeAlias


MODULES = {
    "nodeseek": "nodeseek.nodeseek",
    "deepflood": "deepflood.deepflood",
    "v2ex": "v2ex.v2ex",
}

RECENT_OUTPUT_LINE_LIMIT = 40

RecentOutput: TypeAlias = deque[tuple[str, str]]


class TargetExecutionError(RuntimeError):
    def __init__(
        self,
        *,
        target: str,
        returncode: int | None,
        recent_output: list[tuple[str, str]],
    ) -> None:
        self.target = target
        self.returncode = returncode
        self.recent_output = list(recent_output)
        super().__init__(_format_failure_message(target, returncode, recent_output))


def parse_targets() -> list[str]:
    raw_targets = os.environ.get(
        "CHECKIN_TARGETS",
        "nodeseek,deepflood,v2ex",
    )
    targets = [item.strip().lower() for item in raw_targets.split(",") if item.strip()]

    if not targets:
        raise ValueError("Environment variable CHECKIN_TARGETS is empty")

    unknown = [target for target in targets if target not in MODULES]
    if unknown:
        raise ValueError(
            "Unknown check-in targets: "
            + ", ".join(unknown)
            + ". Supported targets: "
            + ", ".join(MODULES.keys())
        )

    return targets


def _forward_stream(
    stream: IO[str],
    destination: IO[str],
    stream_name: str,
    recent_output: RecentOutput,
) -> None:
    for chunk in iter(stream.readline, ""):
        destination.write(chunk)
        destination.flush()

        line = chunk.rstrip("\r\n")
        if line:
            recent_output.append((stream_name, line))


def _run_target_process(
    target: str,
    module_name: str,
) -> tuple[int, list[tuple[str, str]]]:
    recent_output: RecentOutput = deque(maxlen=RECENT_OUTPUT_LINE_LIMIT)
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", module_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
    except OSError as err:
        recent_output.append(("stderr", f"Failed to start module '{module_name}': {err}"))
        raise TargetExecutionError(
            target=target,
            returncode=None,
            recent_output=list(recent_output),
        ) from err
    assert process.stdout is not None
    assert process.stderr is not None

    stdout_thread = threading.Thread(
        target=_forward_stream,
        args=(process.stdout, sys.stdout, "stdout", recent_output),
    )
    stderr_thread = threading.Thread(
        target=_forward_stream,
        args=(process.stderr, sys.stderr, "stderr", recent_output),
    )

    stdout_thread.start()
    stderr_thread.start()
    returncode = process.wait()
    stdout_thread.join()
    stderr_thread.join()

    return returncode, list(recent_output)


def _format_failure_output_lines(recent_output: list[tuple[str, str]]) -> list[str]:
    if not recent_output:
        return ["  (no stdout/stderr output captured)"]

    return [f"  [{stream_name}] {line}" for stream_name, line in recent_output]


def _format_failure_message(
    target: str,
    returncode: int | None,
    recent_output: list[tuple[str, str]],
) -> str:
    output_lines = "\n".join(_format_failure_output_lines(recent_output))
    return (
        f"{_format_failure_summary(target, returncode)}\n"
        f"Recent output from failed target '{target}':\n"
        f"{output_lines}"
    )


def _format_failure_summary(target: str, returncode: int | None) -> str:
    if returncode is None:
        return f"Check-in target '{target}' failed before it could start"

    return f"Check-in target '{target}' failed with exit code {returncode}"


def _print_failure_output(target: str, recent_output: list[tuple[str, str]]) -> None:
    print(f"Recent output from failed target '{target}':", flush=True)
    for line in _format_failure_output_lines(recent_output):
        print(line, flush=True)


def run_targets(targets: list[str]) -> int:
    for target in targets:
        module_name = MODULES[target]
        print(
            f"Starting check-in target '{target}' ({module_name})",
            flush=True,
        )
        try:
            returncode, recent_output = _run_target_process(target, module_name)
        except TargetExecutionError as err:
            print(_format_failure_summary(err.target, err.returncode), flush=True)
            _print_failure_output(err.target, err.recent_output)
            raise
        if returncode != 0:
            error = TargetExecutionError(
                target=target,
                returncode=returncode,
                recent_output=recent_output,
            )
            print(_format_failure_summary(error.target, error.returncode), flush=True)
            _print_failure_output(error.target, error.recent_output)
            raise error
        print(f"Check-in target '{target}' succeeded", flush=True)
    return 0
