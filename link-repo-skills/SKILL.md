---
name: link-repo-skills
description: Use when enabling selected stored skills for a specific repository by symlinking skill folders into .agents/skills, isolating skill sets per project, avoiding global skill pollution, or verifying Codex scan-ready skill paths.
---

# Link Repo Skills

## Purpose

Expose only the skills a project should use by linking concrete skill folders from a neutral store, usually `$HOME/.ai-agents/skills`, into the current repository's `.agents/skills` directory.

Codex scans `.agents/skills` locations and follows symlinked skill folders. The scan-ready shape must be:

```text
<repo>/.agents/skills/<skill-name>/SKILL.md
```

Do not link a parent namespace such as `.agents/skills/addyosmani/skills/<skill>/SKILL.md`; link each concrete skill directory as its own child of `.agents/skills`.

Default source store is `$HOME/.ai-agents/skills`. The user should not need to mention this path for routine linking.

## Workflow

1. Identify the project root. Default to the current working directory unless the user names a repo path.
2. Identify one or more source directories. If the user names only a collection, resolve it under `$HOME/.ai-agents/skills`; if the user names no source, search `$HOME/.ai-agents/skills`.
3. Link only directories that contain `SKILL.md`.
4. Validate that each resulting `.agents/skills/<name>/SKILL.md` exists through the symlink.
5. Keep `$HOME/.agents/skills` unchanged unless the user explicitly asks for user-global skills.

## Commands

Link every discovered skill from one stored collection into the current repo:

```bash
python3 /Users/egal/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection addyosmani-agent-skills
```

Link only selected skills:

```bash
python3 /Users/egal/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection superpowers \
  --skill using-superpowers \
  --skill test-driven-development
```

Replace the current repo's existing symlinked skills with a new set:

```bash
python3 /Users/egal/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection addyosmani-agent-skills \
  --project /path/to/frontend \
  --clear
```

Preview without changes:

```bash
python3 /Users/egal/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection addyosmani-agent-skills \
  --dry-run
```

## Rules

- Prefer absolute symlinks for personal machine setup; use `--relative` only when the user intends to move the repo and store together.
- Do not ask the user to provide the default store path. Use `--collection <name>` for installed collections under `$HOME/.ai-agents/skills`.
- Accept collection names such as `addyosmani-agent-skills`, `superpowers`, or GitHub shorthand `addyosmani/agent-skills`.
- Safely update existing symlinks, but do not delete real directories or files in `.agents/skills`.
- Use `--clear` only to remove existing symlink entries from the target `.agents/skills`; real directories remain protected.
- If duplicate skill names are detected from the given sources, ask the user to narrow the source path instead of guessing.
