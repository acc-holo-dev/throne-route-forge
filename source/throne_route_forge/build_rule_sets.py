#!/usr/bin/env python3
import argparse
import hashlib
import ipaddress
import json
import re
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RULE_LISTS = ROOT / "rule-lists"
LOCAL_RULES = RULE_LISTS / "local-rules"
EXCLUDED_RULES = RULE_LISTS / "excluded-rules"
EXTERNAL_INCLUDES = RULE_LISTS / "external-includes.json"
EXTERNAL_EXCLUDES = RULE_LISTS / "external-excludes.json"
RELEASE_ASSETS = ROOT / "release-assets"

TARGETS = {
    "proxy/domains": {"kind": "domain", "folder": "proxy", "file": "domains.txt"},
    "proxy/ips": {"kind": "ip", "folder": "proxy", "file": "ip-cidrs.txt"},
    "direct/domains": {"kind": "domain", "folder": "direct", "file": "domains.txt"},
    "direct/ips": {"kind": "ip", "folder": "direct", "file": "ip-cidrs.txt"},
    "reject/domains": {"kind": "domain", "folder": "reject", "file": "domains.txt"},
    "reject/ips": {"kind": "ip", "folder": "reject", "file": "ip-cidrs.txt"},
}

ACCEPTED_SOURCE_TYPES = {
    "domain": {"domain", "domains"},
    "ip": {"ip", "ips", "ip_cidr", "ip-cidr", "cidr"},
}

DOMAIN_RE = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")


def relative(path):
    return path.relative_to(ROOT).as_posix()


def target_path(base, target):
    info = TARGETS[target]
    return base / info["folder"] / info["file"]


def read_text_lines(path):
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def strip_line(line):
    value = line.strip()
    if not value or value.startswith("#"):
        return ""
    for marker in (" #", "\t#"):
        if marker in value:
            value = value.split(marker, 1)[0].strip()
    return value


def normalize_domain(value):
    value = value.strip().lower()
    value = value.removeprefix("http://").removeprefix("https://")
    value = value.split("/", 1)[0]
    value = value.removeprefix(".")
    if not value:
        return None

    for prefix in ("domain:", "suffix:", "keyword:", "regexp:", "regex:"):
        if value.startswith(prefix):
            rule_value = value.split(":", 1)[1].strip()
            if not rule_value:
                return None
            return f"regexp:{rule_value}" if prefix == "regex:" else f"{prefix}{rule_value}"

    if DOMAIN_RE.match(value) or value == "localhost":
        return f"suffix:{value}"
    return None


def normalize_ip(value):
    value = value.strip()
    if not value:
        return None
    try:
        if "/" in value:
            return str(ipaddress.ip_network(value, strict=False))
        ip_obj = ipaddress.ip_address(value)
        suffix = 32 if ip_obj.version == 4 else 128
        return f"{ip_obj}/{suffix}"
    except ValueError:
        return None


def parse_entries(lines, kind, source_name):
    entries = []
    errors = []
    normalizer = normalize_domain if kind == "domain" else normalize_ip

    for number, line in enumerate(lines, start=1):
        raw = strip_line(line)
        if not raw:
            continue
        item = normalizer(raw)
        if item is None:
            errors.append(f"{source_name}:{number}: invalid {kind} entry: {raw}")
        else:
            entries.append(item)
    return entries, errors


def load_source_config(path):
    if not path.exists():
        return [], []
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], [f"{relative(path)}: invalid JSON: {exc}"]

    if not isinstance(config, dict):
        return [], [f"{relative(path)}: root must be an object"]

    sources = config.get("sources", [])
    if not isinstance(sources, list):
        return [], [f"{relative(path)}: sources must be a list"]

    return sources, []


def source_label(config_path, source, index):
    if isinstance(source, dict):
        name = source.get("name") or f"source-{index}"
    else:
        name = f"source-{index}"
    return f"{relative(config_path)}:{name}"


def validate_source_configs(config_path, sources):
    errors = []
    for index, source in enumerate(sources, start=1):
        label = source_label(config_path, source, index)
        if not isinstance(source, dict):
            errors.append(f"{label}: source must be an object")
            continue
        if not source.get("enabled", False):
            continue

        target = source.get("target")
        if target not in TARGETS:
            errors.append(f"{label}: unknown target: {target}")
            continue

        kind = TARGETS[target]["kind"]
        source_type = source.get("type")
        if source_type not in ACCEPTED_SOURCE_TYPES[kind]:
            errors.append(f"{label}: wrong source type for {target}: {source_type}")

        if not source.get("url"):
            errors.append(f"{label}: missing url")
    return errors


def download_source(source):
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "throne-route-forge/1.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read()
    return body.decode("utf-8", errors="replace").splitlines()


def collect_external_entries(config_path, sources, target, kind):
    entries = []
    errors = []
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            continue
        if not source.get("enabled", False) or source.get("target") != target:
            continue
        if source.get("type") not in ACCEPTED_SOURCE_TYPES[kind] or not source.get("url"):
            continue

        label = source_label(config_path, source, index)
        try:
            lines = download_source(source)
        except Exception as exc:
            errors.append(f"{label}: download failed: {exc}")
            continue

        source_entries, parse_errors = parse_entries(lines, kind, label)
        entries.extend(source_entries)
        errors.extend(parse_errors)
    return entries, errors


def build_target(target, include_sources, exclude_sources):
    kind = TARGETS[target]["kind"]
    merged = []
    errors = []

    local_path = target_path(LOCAL_RULES, target)
    entries, parse_errors = parse_entries(read_text_lines(local_path), kind, relative(local_path))
    merged.extend(entries)
    errors.extend(parse_errors)

    external_entries, external_errors = collect_external_entries(EXTERNAL_INCLUDES, include_sources, target, kind)
    merged.extend(external_entries)
    errors.extend(external_errors)

    exclude_path = target_path(EXCLUDED_RULES, target)
    excludes, exclude_errors = parse_entries(read_text_lines(exclude_path), kind, relative(exclude_path))
    errors.extend(exclude_errors)

    external_excludes, external_exclude_errors = collect_external_entries(EXTERNAL_EXCLUDES, exclude_sources, target, kind)
    excludes.extend(external_excludes)
    errors.extend(external_exclude_errors)

    result = sorted(set(merged) - set(excludes))
    return result, errors


def to_rule_set(kind, entries):
    domains = {
        "domain": [],
        "domain_suffix": [],
        "domain_keyword": [],
        "domain_regex": [],
    }
    ip_cidr = []

    for entry in entries:
        if kind == "ip":
            ip_cidr.append(entry)
            continue
        prefix, value = entry.split(":", 1)
        if prefix == "domain":
            domains["domain"].append(value)
        elif prefix == "suffix":
            domains["domain_suffix"].append(value)
        elif prefix == "keyword":
            domains["domain_keyword"].append(value)
        elif prefix == "regexp":
            domains["domain_regex"].append(value)

    rule = {}
    if kind == "ip":
        rule["ip_cidr"] = ip_cidr
    else:
        for key, values in domains.items():
            if values:
                rule[key] = values

    return {"version": 1, "rules": [rule] if rule else []}


def clean_generated_outputs():
    RELEASE_ASSETS.mkdir(exist_ok=True)
    for target in TARGETS:
        stem = target.replace("/", "-")
        for suffix in (".json", ".srs"):
            (RELEASE_ASSETS / f"{stem}{suffix}").unlink(missing_ok=True)
    (RELEASE_ASSETS / "checksums.txt").unlink(missing_ok=True)


def write_outputs(all_entries):
    clean_generated_outputs()
    checksum_lines = []

    for target, entries in all_entries.items():
        kind = TARGETS[target]["kind"]
        output = RELEASE_ASSETS / f"{target.replace('/', '-')}.json"
        output.write_text(
            json.dumps(to_rule_set(kind, entries), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        checksum = hashlib.sha256(output.read_bytes()).hexdigest()
        checksum_lines.append(f"{checksum}  {output.name}")

    (RELEASE_ASSETS / "checksums.txt").write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="fail on invalid entries or failed downloads")
    args = parser.parse_args()

    include_sources, include_config_errors = load_source_config(EXTERNAL_INCLUDES)
    exclude_sources, exclude_config_errors = load_source_config(EXTERNAL_EXCLUDES)

    all_entries = {}
    all_errors = []
    all_errors.extend(include_config_errors)
    all_errors.extend(exclude_config_errors)
    all_errors.extend(validate_source_configs(EXTERNAL_INCLUDES, include_sources))
    all_errors.extend(validate_source_configs(EXTERNAL_EXCLUDES, exclude_sources))

    for target in TARGETS:
        entries, errors = build_target(target, include_sources, exclude_sources)
        all_entries[target] = entries
        all_errors.extend(errors)

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        if args.strict:
            return 1

    write_outputs(all_entries)
    for target, entries in all_entries.items():
        print(f"{target}: {len(entries)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
