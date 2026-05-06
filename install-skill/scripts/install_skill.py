#!/usr/bin/env python3
"""Install a skill and optionally create a Codex-adapted copy."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_STORE = Path.home() / ".ai-agents" / "skills"
INSTALL_AGENT_SKILLS = Path("/Users/egal/.codex/skills/install-agent-skills/scripts/install_agent_skills.py")
GITHUB_SHORTHAND = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def expand(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def parse_adapt_mode(value: str | bool | None) -> str:
    if value is None:
        return "auto"
    if isinstance(value, bool):
        return "true" if value else "false"
    normalized = value.strip().lower()
    if normalized in {"", "auto", "detect", "default"}:
        return "auto"
    if normalized in {"1", "true", "yes", "y", "on"}:
        return "true"
    if normalized in {"0", "false", "no", "n", "off"}:
        return "false"
    raise SystemExit(f"Invalid value for --codex-adapt: {value}. Use auto, true, or false.")


def is_github_shorthand(source: str) -> bool:
    return bool(GITHUB_SHORTHAND.match(source)) and not Path(source).expanduser().exists()


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
        raise SystemExit("Could not infer collection name; pass --name.")
    return slug


def is_simple_name(source: str) -> bool:
    return not any(token in source for token in ("/", ":", "\\")) and not Path(source).expanduser().exists()


def run(cmd: list[str], dry_run: bool) -> None:
    print("+ " + " ".join(cmd))
    if not dry_run:
        subprocess.run(cmd, check=True)


def update_existing(path: Path, dry_run: bool) -> None:
    if (path / ".git").is_dir():
        run(["git", "-C", str(path), "pull", "--ff-only"], dry_run)
    else:
        print(f"= existing non-Git collection: {path}")


def install_base(source: str, name: str | None, store: Path, dry_run: bool) -> tuple[str, Path]:
    collection = name or slug_from_source(source)
    dest = store / collection

    if is_simple_name(source) and (store / source).exists():
        collection = source
        dest = store / source
        update_existing(dest, dry_run)
        return collection, dest

    cmd = ["python3", str(INSTALL_AGENT_SKILLS), source, "--store", str(store)]
    if name:
        cmd.extend(["--name", name])
    if dry_run:
        cmd.append("--dry-run")
    run(cmd, dry_run=False)
    return collection, dest


def find_skill_files(root: Path) -> list[Path]:
    blocked = {".git", ".hg", ".svn", "node_modules", "__pycache__"}
    found: list[Path] = []
    for path in root.rglob("SKILL.md"):
        if any(part in blocked for part in path.parts):
            continue
        found.append(path)
    return sorted(found)


def should_auto_adapt(root: Path) -> tuple[bool, list[str]]:
    markers = {
        "Claude Code": "mentions Claude Code",
        "Claude": "mentions Claude",
        "CLAUDE.md": "uses CLAUDE.md",
        "~/.claude/skills": "uses Claude skills directory",
        "$HOME/.claude/skills": "uses Claude skills directory",
        "TodoWrite": "uses Claude TodoWrite tool",
        "Read tool": "uses Claude Read tool",
        "Edit tool": "uses Claude Edit tool",
        "MultiEdit tool": "uses Claude MultiEdit tool",
        "WebFetch": "uses Claude WebFetch tool",
        "WebSearch": "uses Claude WebSearch tool",
    }
    reasons: list[str] = []
    files = find_skill_files(root)
    for path in files:
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for marker, reason in markers.items():
            if marker in text and reason not in reasons:
                reasons.append(reason)
    return bool(reasons), reasons


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[text.find("\n", end + 1) + 1 :]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"').strip("'")
        data[key.strip()] = value
    return data, body.lstrip("\n")


def normalize_name(value: str, fallback: str) -> str:
    source = value or fallback
    normalized = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")
    return normalized or fallback


def adapt_body(body: str) -> str:
    replacements = {
        "Claude Code": "Codex",
        "Claude": "Codex",
        "CLAUDE.md": "AGENTS.md",
        "~/.claude/skills": "~/.ai-agents/skills",
        "$HOME/.claude/skills": "$HOME/.ai-agents/skills",
        "TodoWrite": "update_plan",
        "Bash tool": "exec_command",
        "Bash": "exec_command",
        "Read tool": "exec_command with sed or rg",
        "Edit tool": "apply_patch",
        "MultiEdit tool": "apply_patch",
        "WebFetch": "web.open",
        "WebSearch": "web.search_query",
    }
    adapted = body
    for old, new in replacements.items():
        adapted = adapted.replace(old, new)
    note = (
        "\n## Codex Adaptation\n\n"
        "- Use Codex tools and repository instructions instead of Claude Code-specific tool names.\n"
        "- Prefer `AGENTS.md` for repo instructions and `~/.ai-agents/skills` for stored skill collections.\n"
    )
    if "## Codex Adaptation" not in adapted:
        adapted = adapted.rstrip() + "\n" + note
    return adapted


def adapt_skill_file(path: Path) -> None:
    text = path.read_text()
    data, body = split_frontmatter(text)
    fallback = path.parent.name
    name = normalize_name(data.get("name", ""), fallback)
    description = data.get("description", "").strip()
    if not description:
        description = f"Use when working with {name.replace('-', ' ')} tasks in Codex."
    description = description.replace("Claude Code", "Codex").replace("Claude", "Codex")
    body = adapt_body(body)
    path.write_text(f"---\nname: {name}\ndescription: {description}\n---\n\n{body}")


def create_adapted_copy(source: Path, collection: str, store: Path, dry_run: bool) -> tuple[str, Path]:
    adapted_name = collection if collection.endswith("-codex") else f"{collection}-codex"
    adapted = store / adapted_name
    print(f"+ refresh Codex-adapted copy {adapted}")
    if dry_run:
        return adapted_name, adapted
    if adapted.exists() or adapted.is_symlink():
        if adapted.is_symlink() or adapted.is_file():
            adapted.unlink()
        else:
            shutil.rmtree(adapted)
    shutil.copytree(
        source,
        adapted,
        symlinks=True,
        ignore=shutil.ignore_patterns(".git", "__pycache__", ".DS_Store"),
    )
    for skill_file in find_skill_files(adapted):
        adapt_skill_file(skill_file)
    return adapted_name, adapted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", help="Skill name, GitHub owner/repo, Git URL, URL, or local directory")
    parser.add_argument("--codex-adapt", default="auto", help="auto/true/false: create a Codex-adapted copy")
    parser.add_argument("--name", help="Collection name under the neutral store")
    parser.add_argument("--store", default=str(DEFAULT_STORE), help="Neutral skill store; defaults to ~/.ai-agents/skills")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without changing files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    store = expand(args.store)
    if not args.dry_run:
        store.mkdir(parents=True, exist_ok=True)

    collection, installed = install_base(args.skill, args.name, store, args.dry_run)
    print(f"\nInstalled collection: {collection}")
    print(f"Installed path: {installed}")

    adapt_mode = parse_adapt_mode(args.codex_adapt)
    should_adapt = adapt_mode == "true"
    if adapt_mode == "auto":
        should_adapt, reasons = should_auto_adapt(installed)
        if should_adapt:
            print("Auto-detected Claude Code-specific markers:")
            for reason in reasons:
                print(f"  - {reason}")
        else:
            print("Auto-detected no Claude Code-specific markers; keeping original collection.")

    if should_adapt:
        adapted_name, adapted_path = create_adapted_copy(installed, collection, store, args.dry_run)
        print(f"Codex-adapted collection: {adapted_name}")
        print(f"Codex-adapted path: {adapted_path}")
        print(f"Link with: $link-repo-skills --collection {adapted_name}")
    else:
        print(f"Link with: $link-repo-skills --collection {collection}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        raise SystemExit(exc.returncode) from exc
