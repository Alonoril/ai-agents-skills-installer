---
name: install-agent-skills
description: Use when installing, importing, updating, or listing agent skill repositories in a neutral local store such as ~/.ai-agents/skills without enabling those skills globally or exposing them to the current repo yet.
---

# Install Agent Skills

## Purpose

Keep third-party or custom skill collections in a neutral store, usually `$HOME/.ai-agents/skills`, so installation is separate from Codex discovery. Do not place installed bundles directly in `$HOME/.agents/skills` unless the user explicitly wants user-global skills.

Use `$link-repo-skills` after installation when a project should expose selected stored skills through its own `.agents/skills` directory.

Default to `$HOME/.ai-agents/skills` when the user does not name a destination. The user should not need to mention this path for routine installs.

## Workflow

1. Resolve the neutral store. Default to `$HOME/.ai-agents/skills` silently; use a repo-local `.ai-agents/skills` only when the user asks for project-local storage.
2. Install or update the source into one named directory under the store.
3. Detect skill folders by locating directories that contain `SKILL.md`.
4. Report detected skill folder paths. Do not symlink them into `.agents/skills` in this skill.
5. If the source contains multiple collections, preserve the collection folder and let `$link-repo-skills` choose which concrete skills to expose.

## Commands

Install or update a Git repository:

```bash
python3 /Users/egal/.codex/skills/install-agent-skills/scripts/install_agent_skills.py \
  addyosmani/agent-skills
```

Install or update Superpowers:

```bash
python3 /Users/egal/.codex/skills/install-agent-skills/scripts/install_agent_skills.py \
  obra/superpowers
```

List detected skills in the store:

```bash
python3 /Users/egal/.codex/skills/install-agent-skills/scripts/install_agent_skills.py --list
```

Use `--store /path/to/.ai-agents/skills` when the user requests a non-default store.

## Rules

- Treat `$HOME/.ai-agents/skills` as the default warehouse, not a Codex scan entry.
- Do not ask the user to provide the default store path. Only use `--store` when the user explicitly names a different location.
- Accept GitHub shorthand such as `addyosmani/agent-skills`; the script stores it as `addyosmani-agent-skills`.
- Keep `.agents/skills/<skill-name>/SKILL.md` creation for `$link-repo-skills`.
- Prefer cloning/updating Git repositories over copying when the source is a Git URL.
- For local sources, create a symlink in the store by default; use `--copy-local` only when the user needs an independent copy.
- After installing, suggest the exact store subpath that should be passed to `$link-repo-skills`.
