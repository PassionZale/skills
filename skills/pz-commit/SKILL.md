---
name: "pz-commit"
description: Create git commits that follow the Conventional Commits specification, use when user asks to "commit", "commit this".
---

创建符合 Conventional Commits 规范的 git commits。

## 核心原则

1. **不要添加任何营销广告** - 禁止在提交信息中添加任何营销广告或推广链接，例如 "Generated with [Claude Code](https://claude.ai/code)"
2. **使用中文** - Subject 和 Body 必须使用中文
3. **简洁明了** - Subject 最多 50 个字符，Body 高度概括
4. **祈使语气** - 使用"添加"而非"添加了"

## 步骤

### 1. 检查暂存状态

运行 `git diff --staged --stat`, 检查暂存更改:

- **存在已暂存的更改** → 这些更改即为提交范围。请勿考虑未暂存或未跟踪的文件——用户已通过暂存操作表明了哪些内容属于此次提交
- **没有暂存任何内容** → 将所有未暂存的修改和未跟踪的文件都视为候选对象。使用会话上下文和差异来决定暂存和提交哪些内容

### 2. 分析暂存内容

```bash
git diff --staged
```

分析：

- 哪些文件更改了
- 更改的性质（功能、修复、重构、文档等）
- 受影响的模块/范围

### 3. 生成提交信息

严格按照此格式生成提交信息：

```
<type>(<scope>): <subject>

<body>
```

#### Type 类型

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

#### Scope 范围

- **有明确范围**：使用模块名（如 `auth`, `api`, `ui`）
- **范围不明确**：省略 scope，直接写 `<type>: <subject>`

#### Subject 主题

- 使用中文
- 最多 50 个字符
- 末尾不加句号
- 祈使语气（"添加"而非"添加了"）

**避免使用**：

- 模糊的主题，如："update"、"fix stuff"
- 过长或重点不突出的主题

#### Body 正文（可选）

- 使用中文
- 简洁明了，高度概括
- 解释做什么和为什么（不是怎么做）

### 4. 创建提交

```bash
git commit -m "<message>"
git log -1 --stat
```

## 示例

```
feat(auth): 添加 JWT 令牌验证
```

```
feat(auth): 添加 JWT 登录流程

- 实现了 JWT 令牌验证逻辑
- 为验证组件添加了文档说明
```

```
docs: 更新 README 安装说明
```
