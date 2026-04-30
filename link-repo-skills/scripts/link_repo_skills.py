#!/usr/bin/env python3
"""Link stored agent skill folders into a project's .agents/skills directory."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path


DEFAULT_STORE = Path.home() / ".ai-agents" / "skills"
GITHUB_SHORTHAND = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def expand(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def normalize_collection_name(name: str) -> str:
    raw = name.strip().rstrip("/")
    if raw.endswith(".git"):
        raw = raw[:-4]
    if GITHUB_SHORTHAND.match(raw):
        owner, repo = raw.split("/", 1)
        return f"{owner}-{repo}".lower()
    return raw


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for path in [current, *current.parents]:
        if (path / ".git").exists():
            return path
    return current


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
        if (current / "SKILL.md").is_file():
            found.append(current)
            continue
        try:
            children = sorted(child for child in current.iterdir() if child.is_dir() and child.name not in blocked)
        except OSError:
            continue
        stack.extend(reversed(children))
    return sorted(found)


def collect_skills(sources: list[Path]) -> dict[str, Path]:
    by_name: dict[str, Path] = {}
    duplicates: dict[str, list[Path]] = {}

    for source in sources:
        if not source.exists():
            raise SystemExit(f"Source does not exist: {source}")
        for skill in find_skill_dirs(source):
            name = skill.name
            if name in by_name:
                duplicates.setdefault(name, [by_name[name]]).append(skill)
            else:
                by_name[name] = skill

    if duplicates:
        lines = ["Duplicate skill names detected; narrow the source path:"]
        for name, paths in sorted(duplicates.items()):
            lines.append(f"  {name}:")
            lines.extend(f"    {path}" for path in paths)
        raise SystemExit("\n".join(lines))

    return by_name


def remove_symlinked_entries(dest: Path, dry_run: bool) -> None:
    if not dest.exists():
        return
    for entry in sorted(dest.iterdir()):
        if entry.is_symlink():
            print(f"+ unlink {entry}")
            if not dry_run:
                entry.unlink()


def make_link_target(target: Path, link: Path, relative: bool) -> Path:
    if not relative:
        return target.resolve()
    return Path(os.path.relpath(target.resolve(), start=link.parent.resolve()))


def link_skill(name: str, target: Path, dest: Path, relative: bool, dry_run: bool) -> None:
    link = dest / name
    link_target = make_link_target(target, link, relative)

    if link.exists() or link.is_symlink():
        if link.is_symlink():
            current = link.resolve()
            if current == target.resolve():
                print(f"= {link} -> {target}")
                return
            print(f"+ unlink {link}")
            if not dry_run:
                link.unlink()
        else:
            raise SystemExit(f"Refusing to replace non-symlink path: {link}")

    print(f"+ symlink {link} -> {link_target}")
    if not dry_run:
        link.symlink_to(link_target, target_is_directory=True)
        if not (link / "SKILL.md").is_file():
            raise SystemExit(f"Created link but SKILL.md is not reachable: {link}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "sources",
        nargs="*",
        default=[str(DEFAULT_STORE)],
        help="Stored skill folder, collection root, or skills directory",
    )
    parser.add_argument("--store", default=str(DEFAULT_STORE), help="Neutral skill store directory")
    parser.add_argument(
        "--collection",
        action="append",
        default=[],
        help="Collection name under the neutral store; accepts names like addyosmani-agent-skills or addyosmani/agent-skills",
    )
    parser.add_argument("--project", default=".", help="Project path; defaults to current directory")
    parser.add_argument("--dest", help="Override destination skills directory")
    parser.add_argument("--skill", action="append", default=[], help="Skill folder name to link; repeatable")
    parser.add_argument("--clear", action="store_true", help="Remove existing symlink entries from destination first")
    parser.add_argument("--relative", action="store_true", help="Create relative symlinks instead of absolute symlinks")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without changing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project = find_repo_root(expand(args.project))
    dest = expand(args.dest) if args.dest else project / ".agents" / "skills"
    store = expand(args.store)
    if args.collection:
        sources = [store / normalize_collection_name(collection) for collection in args.collection]
        if args.sources != [str(DEFAULT_STORE)]:
            sources.extend(expand(source) for source in args.sources)
    else:
        sources = [expand(source) for source in args.sources]

    skills = collect_skills(sources)
    if args.skill:
        missing = sorted(set(args.skill) - set(skills))
        if missing:
            raise SystemExit("Requested skills not found: " + ", ".join(missing))
        selected = {name: skills[name] for name in args.skill}
    else:
        selected = skills

    if not selected:
        raise SystemExit("No skill folders with SKILL.md found in the given sources.")

    print(f"Project: {project}")
    print(f"Destination: {dest}")
    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)
    if args.clear:
        remove_symlinked_entries(dest, args.dry_run)

    for name, target in sorted(selected.items()):
        link_skill(name, target, dest, args.relative, args.dry_run)

    print("\nScan-ready skill paths:")
    for name in sorted(selected):
        print(f"  {dest / name / 'SKILL.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
