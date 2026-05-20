---
name: "git-commit"
description: 创建符合 Conventional Commits 规范的 git commit. 当用户说 "commit", "commit this", "make a commit" 时触发.
---

创建符合 Conventional Commits 规范的 git commit.

## 核心原则

1. **不要添加任何营销广告** - 禁止在提交信息中添加任何广告或推广链接，例如 "Generated with [Claude Code](https://claude.ai/code)"
2. **使用中文** - Subject 和 Body 必须使用中文

---

## 步骤 1 — 检查暂存状态

```bash
git diff --staged --stat
```

**决策逻辑：**

- 如果存在已暂存的更改 → 仅将这些更改作为提交范围；完全忽略未暂存和未跟踪的文件
- 如果没有暂存任何内容 → 将所有修改和未跟踪的文件作为候选；使用会话上下文和差异来决定暂存哪些文件

---

## 步骤 2 — 分析差异

```bash
git diff --staged
```

提取：

- 哪些文件发生了变化
- 每个更改的性质（新功能、错误修复、重构、文档等）
- 受影响的模块或范围

---

## 步骤 3 — 生成提交信息

使用以下格式：

```
<type>(<scope>): <subject>

<body>
```

### Type 类型

- **feat**: 新功能
- **fix**: 修复 bug
- **docs**: 仅文档更改
- **style**: 格式化、空格等
- **refactor**: 代码重构
- **perf**: 性能改进
- **test**: 添加或更新测试
- **chore**: 维护任务、依赖更新
- **ci**: CI 配置更改
- **build**: 构建系统更改
- **revert**: 回退提交

### Scope 范围

- 有明确范围 -> 使用模块名（如 `auth`, `api`, `ui`）
- 范围不明确 -> 省略 scope，直接写 `<type>: <subject>`

### Subject 主题

- 最多 50 个字符
- 末尾不加句号
- 祈使语气（"添加"而非"添加了"）

**避免使用**：

- 模糊的主题，如："update"、"fix stuff"
- 过长或重点不突出的主题

### Body 正文（可选）

- 简洁明了，高度概括
- 解释做什么和为什么（不是怎么做）

---

## Step 4 — 执行提交

```bash
git commit -m "<message>"
```

---

## 示例

最简格式：

```
feat(auth): 添加 JWT 令牌验证
```

带正文：

```
feat(auth): 添加 JWT 登录流程

实现令牌验证逻辑，为验证组件补充文档说明
```

无范围：

```
docs: 更新 README 安装说明
```
