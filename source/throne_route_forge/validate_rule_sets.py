#!/usr/bin/env python3
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE_ASSETS = ROOT / "release-assets"
RULE_SET_FILES = (
    "proxy-domains.json",
    "proxy-ips.json",
    "direct-domains.json",
    "direct-ips.json",
    "reject-domains.json",
    "reject-ips.json",
)


def main():
    bad = []
    for name in RULE_SET_FILES:
        path = RELEASE_ASSETS / name
        if not path.exists():
            bad.append(f"{path}: missing generated rule-set")
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            bad.append(f"{path}: invalid JSON: {exc}")
            continue

        if data.get("version") != 1:
            bad.append(f"{path}: missing version=1")

        rules = data.get("rules")
        if not isinstance(rules, list):
            bad.append(f"{path}: rules must be a list")
            continue

        for index, rule in enumerate(rules, start=1):
            if not isinstance(rule, dict):
                bad.append(f"{path}: rule {index} must be an object")

    for issue in bad:
        print(issue, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
