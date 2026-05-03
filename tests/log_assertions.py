import re


LOG_PREFIX_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \(UTC[+-]\d{2}:\d{2}\) "
)


def assert_timestamped_lines(output: str) -> list[str]:
    lines = [line for line in output.splitlines() if line]
    assert lines
    assert all(LOG_PREFIX_PATTERN.match(line) for line in lines)
    return lines
