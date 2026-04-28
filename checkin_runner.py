import os
import subprocess
import sys


MODULES = {
    "nodeseek": "nodeseek.nodeseek",
    "deepflood": "deepflood.deepflood",
    "v2ex": "v2ex.v2ex",
}


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


def run_targets(targets: list[str]) -> int:
    for target in targets:
        print(f"Running target: {target}", flush=True)
        result = subprocess.run([sys.executable, "-m", MODULES[target]], check=False)
        if result.returncode != 0:
            return result.returncode
    return 0
