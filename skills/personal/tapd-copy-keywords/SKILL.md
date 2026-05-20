---
name: tapd-copy-keywords
description: 创建符合 Conventional Commits 规范的 git commit，自动关联 TAPD 代办需求的源码关键字。
disable-model-invocation: true
---

创建符合 Conventional Commits 规范的 git commit，自动关联 TAPD 代办需求的源码关键字。

## 核心原则

- 零广告：禁止在提交信息中添加任何推广链接或模型标识
- 仅处理已暂存：无暂存更改时提示用户 `git add` 并退出
- 纯中文：Subject 和 Body 必须使用简体中文
- 精简规范：Subject ≤ 50 字符，末尾无标点，严格使用祈使句
- 智能关联：优先使用传入的 story_id，未提供时尝试匹配，不强制关联

## 输入参数

- `--s <story_id>` (number, 可选): TAPD 需求 ID
- `--w <workspace_id>` (number, 可选): TAPD 工作空间 ID

## 脚本目录

脚本位于 `scripts/` 子目录。`${BASE_DIR}` = 本 SKILL.md 所在目录。将 `${BASE_DIR}` 替换为实际值。

## 执行步骤

### Step 0 - 验证暂存状态

1. 执行 `git diff --staged --stat`
2. 若无输出 → 提示“工作区暂无已暂存更改，请先使用 `git add`”并终止
3. 若有输出 → 记录变更清单，进入 Step 1

### Step 1 - 分析代码变更

1. 执行 `git diff --staged`
2. 提取关键信息：变更类型倾向、影响模块（scope）、核心改动逻辑

### Step 2 - 获取 TAPD 源码关键字

- **已指定 `story_id`**：直接执行 `python3 ${BASE_DIR}/scripts/get_scm_copy_keywords.py --s <story_id>` 获取关键字。
- **未指定 `story_id`**：
  1. 执行 `python3 ${BASE_DIR}/scripts/get_user_todo_story.py --w <workspace_id>（若提供）` 获取当前代办列表。
  2. 结合 Step 1 的变更语义，**尝试匹配**最相关的 `story_id`。
     - **匹配规则**：仅在代码变更与代办需求描述存在**明确且高度相关**的语义关联时才进行匹配。若关联模糊、存在多义或置信度不足，**直接放弃匹配，严禁猜测或强制关联**。若能同时匹配多个, 让用户手动选择，**必须使用 AskUserQuestion 工具以交互式选择的方式呈现选项，而非纯文本表格**。
  3. 匹配成功 → 使用对应 ID 执行 `python3 ${BASE_DIR}/scripts/get_scm_copy_keywords.py --s <matched_story_id> --w <matched_workspace_id>`。
  4. 匹配失败 → 跳过关键字获取流程。
- **统一容错**：脚本执行异常、返回为空或主动放弃匹配时，Footer 留空，直接进入 Step 3。

### Step 3 - 生成 Commit Message

**严格按照此格式生成：**
<type>(<scope>): <subject>

<body>

<footer>

**规则约束：**

- Type: 严格从 `[feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert]` 中选择
- Scope: 明确模块名则保留括号；不明确则省略，格式为 `<type>: <subject>`
- Subject: ≤50 字符，中文祈使句，无句号，禁用模糊词
- Body: 可选。以 `- ` 开头分点说明“做什么”和“为什么”
- Footer: 直接粘贴 Step 2 获取的关键字。若为空，则省略 Footer 及其上方的空行

### Step 4 - 执行提交与验证

1. 将 Step 3 生成的完整内容通过标准输入传入 Git：
   `printf '%s' "<完整提交信息>" | git commit -F -`
2. 验证结果：`git log -1 --oneline`
3. 向用户返回最终提交信息

## 示例

**关联 TAPD 关键字：**

```
feat(auth): 添加 JWT 登录流程

- 实现令牌验证逻辑
- 验证组件补充文档说明

--story=1040462@tapd-40888836 --user=张三 JWT 登录流程开发 https://www.tapd.cn/40888836/s/2547032
```

**标准提交（无关键字/无明确 scope）：**

```
docs: 更新 README 安装说明

- 补充本地环境依赖安装步骤
- 修正 Docker 启动命令示例
```
