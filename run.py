import os
import subprocess
import sys


MODULES = {
    "nodeseek": "nodeseek.nodeseek",
    "deepflood": "deepflood.deepflood",
    "v2ex": "v2ex.v2ex",
    "onepoint3acres": "onepoint3acres.onepoint3acres",
}


def parse_targets() -> list[str]:
    raw_targets = os.environ.get(
        "CHECKIN_TARGETS",
        "nodeseek,deepflood,v2ex,onepoint3acres",
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


if __name__ == "__main__":
    try:
        for target in parse_targets():
            print(f"Running target: {target}", flush=True)
            result = subprocess.run([sys.executable, "-m", MODULES[target]], check=False)
            if result.returncode != 0:
                sys.exit(result.returncode)
    except Exception as err:
        print(err, flush=True)
        sys.exit(1)

