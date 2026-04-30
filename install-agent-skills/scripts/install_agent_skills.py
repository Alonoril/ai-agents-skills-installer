#!/usr/bin/env python3
"""Install or update agent skill repositories in a neutral local store."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_STORE = Path.home() / ".ai-agents" / "skills"
GITHUB_SHORTHAND = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def expand(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def slug_from_source(source: str) -> str:
    if is_github_shorthand(source):
        owner, repo = source.split("/", 1)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"{owner}-{repo}".lower()

    parsed = urlparse(source)
    if parsed.scheme and parsed.netloc.lower() == "github.com":
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 2:
            owner = parts[-2]
            repo = parts[-1][:-4] if parts[-1].endswith(".git") else parts[-1]
            return f"{owner}-{repo}".lower()

    raw = Path(parsed.path).name if parsed.scheme else Path(source).name
    if raw.endswith(".git"):
        raw = raw[:-4]
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip(".-_").lower()
    if not slug:
        raise SystemExit("Could not infer --name from source; provide --name explicitly.")
    return slug


def is_github_shorthand(source: str) -> bool:
    return bool(GITHUB_SHORTHAND.match(source)) and not Path(source).expanduser().exists()


def normalize_source(source: str) -> str:
    if is_github_shorthand(source):
        return f"https://github.com/{source}.git"
    return source


def is_git_url(source: str) -> bool:
    if source.startswith(("git@", "ssh://", "git://")):
        return True
    parsed = urlparse(source)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def run(cmd: list[str], dry_run: bool) -> None:
    print("+ " + " ".join(cmd))
    if not dry_run:
        subprocess.run(cmd, check=True)


def is_skill_dir(path: Path) -> bool:
    return (path / "SKILL.md").is_file()


def find_skill_dirs(root: Path) -> list[Path]:
    if not root.exists():
        return []
    found: list[Path] = []
    visited: set[Path] = set()
    blocked = {".git", ".hg", ".svn", "node_modules"}
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            real = current.resolve()
        except OSError:
            continue
        if real in visited:
            continue
        visited.add(real)
        if is_skill_dir(current):
            found.append(current)
            continue
        try:
            children = sorted(child for child in current.iterdir() if child.is_dir() and child.name not in blocked)
        except OSError:
            continue
        stack.extend(reversed(children))
    return sorted(found)


def install_git(source: str, dest: Path, branch: str | None, depth: int | None, no_pull: bool, dry_run: bool) -> None:
    if dest.exists():
        if not (dest / ".git").is_dir():
            raise SystemExit(f"Destination exists but is not a Git repo: {dest}")
        if no_pull:
            print(f"Already installed: {dest}")
            return
        cmd = ["git", "-C", str(dest), "pull", "--ff-only"]
        run(cmd, dry_run)
        return

    cmd = ["git", "clone"]
    if depth:
        cmd += ["--depth", str(depth)]
    if branch:
        cmd += ["--branch", branch]
    cmd += [source, str(dest)]
    run(cmd, dry_run)


def install_local(source: Path, dest: Path, copy_local: bool, dry_run: bool) -> None:
    if not source.exists() or not source.is_dir():
        raise SystemExit(f"Local source is not a directory: {source}")
    if dest.exists() or dest.is_symlink():
        if dest.is_symlink() and dest.resolve() == source.resolve():
            print(f"Already installed: {dest} -> {source}")
            return
        raise SystemExit(f"Destination already exists: {dest}")

    if copy_local:
        print(f"+ copytree {source} {dest}")
        if not dry_run:
            shutil.copytree(source, dest, symlinks=True)
        return

    print(f"+ symlink {dest} -> {source}")
    if not dry_run:
        dest.symlink_to(source, target_is_directory=True)


def list_skills(store: Path) -> None:
    skills = find_skill_dirs(store)
    if not skills:
        print(f"No skill folders found under {store}")
        return
    for skill in skills:
        print(skill)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", help="Git URL, GitHub owner/repo shorthand, or local directory to install")
    parser.add_argument("--store", default=str(DEFAULT_STORE), help="Neutral skill store directory")
    parser.add_argument("--name", help="Store subdirectory name; inferred from source when omitted")
    parser.add_argument("--branch", help="Git branch or tag to clone")
    parser.add_argument("--depth", type=int, default=1, help="Git clone depth; set 0 for full clone")
    parser.add_argument("--no-pull", action="store_true", help="Do not pull when destination Git repo already exists")
    parser.add_argument("--copy-local", action="store_true", help="Copy local source instead of symlinking it")
    parser.add_argument("--list", action="store_true", help="List detected skill folders in the store")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without changing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    store = expand(args.store)

    if args.list:
        list_skills(store)
        return 0
    if not args.source:
        raise SystemExit("Provide a source or use --list.")

    source = normalize_source(args.source)
    name = args.name or slug_from_source(args.source)
    dest = store / name
    if not args.dry_run:
        store.mkdir(parents=True, exist_ok=True)

    if is_git_url(source):
        depth = args.depth if args.depth > 0 else None
        install_git(source, dest, args.branch, depth, args.no_pull, args.dry_run)
    else:
        install_local(expand(source), dest, args.copy_local, args.dry_run)

    print(f"\nInstalled location: {dest}")
    skills = find_skill_dirs(dest)
    if skills:
        print("Detected skill folders:")
        for skill in skills:
            print(f"  {skill}")
    else:
        print("No SKILL.md folders detected yet.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
