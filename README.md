# Agent Skills 使用说明

本文说明两个全局 Codex skill 的使用方式：

- `$install-agent-skills`：把 skill 仓库安装或更新到中立目录 `~/.ai-agents/skills`
- `$link-repo-skills`：把中立目录里的具体 skill 按需链接到某个项目的 `.agents/skills`

核心原则：

```text
~/.ai-agents/skills/                 # skill 仓库，不直接给 Codex 扫描
<project>/.agents/skills/<skill>/    # 项目实际启用的 skill，Codex 会扫描
```

不要把所有 skill 都装进全局扫描目录。按项目用 symlink 暴露需要的 skill，隔离效果最稳定。

日常使用时不需要在提示词里写 `~/.ai-agents/skills`。两个 skill 都默认使用这个中立目录；只有要改用其他目录时才需要显式说明。

## 1. 安装 skill 仓库

安装 addyosmani/agent-skills：

```bash
rtk python3 /Users/${user_name}/.codex/skills/install-agent-skills/scripts/install_agent_skills.py \
  addyosmani/agent-skills
```

安装 Superpowers：

```bash
rtk python3 /Users/${user_name}/.codex/skills/install-agent-skills/scripts/install_agent_skills.py \
  obra/superpowers
```

说明：

- 默认安装位置是 `~/.ai-agents/skills`
- 如果目标目录已存在且是 Git 仓库，脚本会执行 `git pull --ff-only`
- 安装完成后，脚本会列出检测到的 `SKILL.md` 目录
- 在普通终端中可以去掉 `rtk` 前缀；在当前 Codex 工作区内执行命令时保留 `rtk`

列出当前中立仓库中检测到的 skills：

```bash
rtk python3 /Users/${user_name}/.codex/skills/install-agent-skills/scripts/install_agent_skills.py --list
```

使用非默认中立目录：

```bash
rtk python3 /Users/${user_name}/.codex/skills/install-agent-skills/scripts/install_agent_skills.py \
  https://github.com/addyosmani/agent-skills.git \
  --name addyosmani-agent-skills \
  --store /path/to/.ai-agents/skills
```

## 2. 给项目启用 skills

进入项目目录后，把某个集合下的所有 skills 链接到当前 repo：

```bash
rtk python3 /Users/${user_name}/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection addyosmani-agent-skills
```

给指定项目启用：

```bash
rtk python3 /Users/${user_name}/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection addyosmani-agent-skills \
  --project /path/to/frontend
```

只启用指定 skills：

```bash
rtk python3 /Users/${user_name}/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection superpowers \
  --project /path/to/backend \
  --skill using-superpowers \
  --skill test-driven-development \
  --skill systematic-debugging
```

替换项目当前已链接的 skills：

```bash
rtk python3 /Users/${user_name}/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection addyosmani-agent-skills \
  --project /path/to/frontend \
  --clear
```

`--clear` 只删除 `.agents/skills` 里的 symlink，不会删除真实目录或真实文件。

预览将要执行的链接操作：

```bash
rtk python3 /Users/${user_name}/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection addyosmani-agent-skills \
  --project /path/to/frontend \
  --dry-run
```

## 3. 典型场景

### 前端项目只使用 addyosmani/agent-skills

```bash
rtk python3 /Users/${user_name}/.codex/skills/install-agent-skills/scripts/install_agent_skills.py \
  addyosmani/agent-skills

rtk python3 /Users/${user_name}/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection addyosmani-agent-skills \
  --project /path/to/frontend \
  --clear
```

结果形态：

```text
/path/to/frontend/.agents/skills/<addy-skill-name>/SKILL.md
```

这个项目不会因为 `~/.ai-agents/skills` 中同时存在 Superpowers 而自动看到 Superpowers。

### 后端项目只使用 Superpowers

```bash
rtk python3 /Users/${user_name}/.codex/skills/install-agent-skills/scripts/install_agent_skills.py \
  obra/superpowers

rtk python3 /Users/${user_name}/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection superpowers \
  --project /path/to/backend \
  --clear
```

如只想启用一部分 Superpowers skill，加多个 `--skill`。

## 4. 在 Codex 对话里怎么调用

安装或更新 skill 仓库时，可以直接说：

```text
使用 $install-agent-skills 安装 addyosmani/agent-skills
```

给当前 repo 启用一组 skills 时，可以直接说：

```text
使用 $link-repo-skills 把 addyosmani-agent-skills 链接到当前项目
```

只启用指定 skills：

```text
使用 $link-repo-skills 只把 using-superpowers 和 systematic-debugging 链接到这个后端项目
```

Codex 会读取对应全局 skill，并使用其中的脚本执行安装或链接。

## 5. 验证

检查某个项目实际启用了哪些 skills：

```bash
rtk find /path/to/project/.agents/skills -maxdepth 2 -name SKILL.md -print
```

每个启用的 skill 都应该满足：

```text
/path/to/project/.agents/skills/<skill-name>/SKILL.md
```

不要使用这种结构：

```text
/path/to/project/.agents/skills/addyosmani/skills/<skill-name>/SKILL.md
```

原因是 Codex 最稳的扫描形态是 `.agents/skills` 下直接一层一个 skill。

## 6. Git 建议

如果 `.agents/skills` 是个人本机配置，不想提交：

```gitignore
.agents/skills/
```

如果团队要共享项目应该启用哪些 skills，优先考虑：

- 直接提交 repo-scoped skill 内容
- 使用相对 symlink
- 使用 submodule 或项目脚本统一安装

不要提交指向 `$HOME/.ai-agents/...` 的绝对 symlink 给团队使用，因为其他人的机器路径通常不同。

## 7. 常见问题

### 为什么不直接装到 ~/.agents/skills？

`~/.agents/skills` 是用户级全局扫描入口。装进去后，所有项目都可能看到这些 skills，不利于前后端项目隔离。

### 为什么要一个 skill 一个 symlink？

Codex 识别 skill 的稳定形态是：

```text
.agents/skills/<skill-name>/SKILL.md
```

把整个集合挂成 `.agents/skills/some-bundle/...` 会依赖递归扫描实现细节，不如直接链接具体 skill 目录稳。

### 已经链接过，再运行会怎样？

如果 symlink 已经指向同一个目标，脚本会跳过。

如果 symlink 指向旧目标，脚本会更新它。

如果目标位置是真实目录或真实文件，脚本会拒绝覆盖。

### 怎么先确认不会误改？

加 `--dry-run`。

```bash
rtk python3 /Users/${user_name}/.codex/skills/link-repo-skills/scripts/link_repo_skills.py \
  --collection addyosmani-agent-skills \
  --project /path/to/frontend \
  --clear \
  --dry-run
```
