---
name: install-skill
description: Use when the user asks to install a skill by skill name, GitHub owner/repo, Git URL, or URL, especially when they provide placeholder parameters like {skill} and {codex_adapt} or ask whether a Claude Code skill should be adapted for Codex.
---

# Install Skill

## Inputs

- `{skill}`: skill name already in `~/.ai-agents/skills`, GitHub shorthand such as `owner/repo`, Git URL, HTTPS URL, or local directory.
- `{codex_adapt}`: optional. Use `auto` or omit it to detect Claude Code-specific markers; use `true` to force a Codex-adapted copy; use `false` to keep the original unchanged.

## Command

```bash
python3 /Users/egal/.codex/skills/install-skill/scripts/install_skill.py \
  "{skill}"
```

## Rules

- Default store is `~/.ai-agents/skills`; do not ask the user to provide it.
- Always use `/Users/egal/.codex/skills/install-agent-skills/scripts/install_agent_skills.py` for the base install/update.
- If `{codex_adapt}` is omitted, use `--codex-adapt auto`.
- In `auto`, scan installed `SKILL.md` files for Claude Code markers such as `Claude Code`, `CLAUDE.md`, `TodoWrite`, `Read tool`, `Edit tool`, `WebFetch`, or `~/.claude/skills`.
- If `{codex_adapt}=false`, keep the installed skill unchanged.
- If `{codex_adapt}=true`, create or refresh `<installed-name>-codex` in the same store and leave the original untouched.
- For already installed simple names, update the Git repo when possible; otherwise treat the existing directory as the source.
- Report the installed path and, when adapted, the adapted collection name to use with `$link-repo-skills`.
