import sys

from checkin_runner import parse_targets, run_targets
from runtime_log import log


if __name__ == "__main__":
    try:
        sys.exit(run_targets(parse_targets()))
    except Exception as err:
        log(err)
        sys.exit(1)
