"""Safety-check and ZIP the existing project tree, including complete .git history."""

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT.parent / "26210660035-刘思颖-final-project.zip"
SECRET = re.compile(rb"(?:sk-[A-Za-z0-9_-]{20,}|gh[opusr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
FORBIDDEN = {".env", "config.toml"}
FORBIDDEN_SUFFIXES = {".xlsx", ".xls", ".pem", ".key"}
EPHEMERAL = {"__pycache__", ".pytest_cache", ".venv", ".DS_Store"}


def git(*args):
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT)
    args = parser.parse_args()
    if git("status", "--porcelain", "--untracked-files=all"):
        raise SystemExit("Working tree is not clean; commit final changes first")
    if git("rev-parse", "--is-shallow-repository") != "false":
        raise SystemExit("Repository is shallow; full Git history required")
    if int(git("rev-list", "--count", "HEAD")) < 3:
        raise SystemExit("Expected meaningful multi-commit history")
    tracked = git("ls-files").splitlines()
    for name in tracked:
        path = ROOT / name
        if path.name in FORBIDDEN or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise SystemExit(f"Forbidden tracked data/credential file: {name}")
        if SECRET.search(path.read_bytes()):
            raise SystemExit(f"Potential secret in tracked file: {name}")
    history = subprocess.run(["git", "-C", str(ROOT), "log", "-p", "--all", "--no-ext-diff"],
                             capture_output=True, check=True).stdout
    if SECRET.search(history):
        raise SystemExit("Potential secret in Git commit history")
    objects = git("rev-list", "--objects", "--all").splitlines()
    for obj in objects:
        name = obj.partition(" ")[2]
        if name and (Path(name).name in FORBIDDEN or Path(name).suffix.lower() in FORBIDDEN_SUFFIXES):
            raise SystemExit(f"Forbidden file in Git history: {name}")
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        raise SystemExit("ZIP must be outside the project folder")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in sorted(ROOT.rglob("*")):
            rel = path.relative_to(ROOT)
            if any(part in EPHEMERAL for part in rel.parts):
                continue
            if any(part in ("private_data", "private_runs") for part in rel.parts):
                raise SystemExit(f"Private folder found in project: {rel}")
            if path.is_file():
                if path.name in FORBIDDEN or path.suffix.lower() in FORBIDDEN_SUFFIXES:
                    raise SystemExit(f"Forbidden local file in project: {rel}")
                archive.write(path, arcname=f"{ROOT.name}/{rel}")
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        if not any(name.startswith(f"{ROOT.name}/.git/objects/") for name in names):
            raise SystemExit("ZIP missing .git objects")
    print(f"Created {output} ({output.stat().st_size:,} bytes, {len(names)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

