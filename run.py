import sys

from checkin_runner import parse_targets, run_targets


if __name__ == "__main__":
    try:
        sys.exit(run_targets(parse_targets()))
    except Exception as err:
        print(err, flush=True)
        sys.exit(1)
