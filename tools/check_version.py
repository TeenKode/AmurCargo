"""Enforce one monotonically increasing project version and matching HTML badges."""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
BADGE = re.compile(r'<span\b[^>]*\bdata-project-version="([^"]+)"[^>]*>\s*v([^<]+)\s*</span>')
HTML_FILES = (
    "START.html",
    "OFFLINE.html",
    "simulator/Open_Simulation_3D.html",
)


def parse_version(value):
    if not isinstance(value, str) or not SEMVER.fullmatch(value):
        raise ValueError(f"Invalid SemVer (expected MAJOR.MINOR.PATCH): {value!r}")
    return tuple(map(int, value.split(".")))


def package_version():
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    version = pkg["version"]
    parse_version(version)
    if lock.get("version") != version or lock.get("packages", {}).get("", {}).get("version") != version:
        raise ValueError("package-lock.json must match package.json; run npm version patch --no-git-tag-version")
    return version


def extract_badge(html):
    matches = BADGE.findall(html)
    if len(matches) != 1 or matches[0][0] != matches[0][1].strip():
        raise ValueError(f"Expected exactly one matching project version badge; found {matches!r}")
    return matches[0][0]


def check_html(version):
    for file in HTML_FILES:
        actual = extract_badge((ROOT / file).read_text(encoding="utf-8"))
        if actual != version:
            raise ValueError(f"{file} has v{actual}; expected v{version}")
        print(f"OK {file}: v{actual}")


def check_base(base, version):
    previous = subprocess.check_output(
        ["git", "show", f"{base}:package.json"], cwd=ROOT, text=True
    )
    base_version = json.loads(previous)["version"]
    if parse_version(version) <= parse_version(base_version):
        raise ValueError(
            f"Version must increase in every PR: main has {base_version}, PR has {version}. "
            "Run npm version patch --no-git-tag-version"
        )
    print(f"OK version bump: {base_version} -> {version}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="Git ref to compare against, e.g. origin/main")
    parser.add_argument("--check-html", action="store_true")
    args = parser.parse_args()
    version = package_version()
    if args.base:
        check_base(args.base, version)
    if args.check_html:
        check_html(version)
    print(f"Project version: v{version}")


if __name__ == "__main__":
    main()
