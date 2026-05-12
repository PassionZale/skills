---
name: "pz-commit"
description: Create git commits following the Conventional Commits specification. Use when the user says "commit", "commit this", "make a commit".
---

## Commit Generator

Creates well-structured git commits following the [Conventional Commits](https://www.conventionalcommits.org/) specification.

## Constraints

- **No marketing footers** — never append lines like `Generated with Claude Code (https://claude.ai/code)` or any promotional content to commit messages.
- **Chinese subject and body** — the `<subject>` and `<body>` must be written in Chinese.
- **Imperative mood** — use "添加" not "添加了", "修复" not "修复了".
- **Subject ≤ 50 characters** — no trailing period.

---

## Step 1 — Inspect staged state

```bash
git diff --staged --stat
```

**Decision logic:**

- If staged changes exist → treat only those as the commit scope; ignore unstaged and untracked files entirely.
- If nothing is staged → treat all modified and untracked files as candidates; use session context and diffs to decide what to stage.

---

## Step 2 — Analyze the diff

```bash
git diff --staged
```

Extract:

- Which files changed
- Nature of each change (feature, bug fix, refactor, docs, etc.)
- Affected module or scope

---

## Step 3 — Construct the commit message

Use the following format:

```
<type>(<scope>): <subject>

<body>
```

### type

| Value      | When to use                              |
| ---------- | ---------------------------------------- |
| `feat`     | New feature                              |
| `fix`      | Bug fix                                  |
| `docs`     | Documentation only                       |
| `style`    | Formatting, whitespace, no logic change  |
| `refactor` | Code restructure without behavior change |
| `perf`     | Performance improvement                  |
| `test`     | Adding or updating tests                 |
| `chore`    | Maintenance, dependency updates          |
| `ci`       | CI/CD configuration changes              |
| `build`    | Build system changes                     |
| `revert`   | Reverting a previous commit              |

### scope

- Use the affected module name when clear (e.g., `auth`, `api`, `ui`).
- Omit scope entirely when changes span multiple modules or the scope is unclear.

### subject (中文)

- Written in Chinese, imperative mood
- ≤ 50 characters, no trailing period
- Be specific — avoid vague messages like "update" or "fix stuff"

### body (中文, optional)

- Written in Chinese
- Explain _what_ changed and _why_, not _how_
- Keep it concise — high-level summary only

---

## Step 4 — Create the commit

```bash
git commit -m "<message>"
git log -1 --stat
```

---

## Examples

Minimal:

```
feat(auth): 添加 JWT 令牌验证
```

With body:

```
feat(auth): 添加 JWT 登录流程

实现令牌验证逻辑，为验证组件补充文档说明
```

No scope:

```
docs: 更新 README 安装说明
```
