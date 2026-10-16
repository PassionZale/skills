---
name: tapd-story-setup
description: 加载 TAPD 需求物料并使当前会话进入开发就绪状态。当用户提供 short_id 并要求 setup 需求、加载需求物料、准备开发某需求时触发。
disable-model-invocation: true
---

根据 short_id 加载 `${TAPD_STORY_ROOT}/stories/<short_id>/` 下的需求物料，处理 feature branch，使当前会话进入开发就绪状态。

- `TAPD_STORY_ROOT`：breakdown 工作区的根目录（tapd-story-breakdown 通常在独立 workspace 执行，与开发 repo 分离），通过 `~/.passionzale-skills/.env` 配置
- 前置条件：已通过 `/tapd-story-breakdown` 拉取过该需求的物料。本 skill 只消费物料，不做任何拉取

## 输入

用户的请求应包含:

- 需求短 ID: short_id (number)

```
/tapd-story-setup <short_id>
```

## 用户输入工具

当此 skill 需要向用户提问时，按以下优先级规则选择工具：

1. **优先使用内置工具**：使用当前 agent runtime 提供的内置用户输入工具，例如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或任何等效工具。
2. **降级方案**：如果没有任何内置工具可用，则输出带编号的纯文本消息，让用户回复数字/答案。
3. **批量提问**：如果工具支持一次问多个问题，则合并到一次调用中；如果只支持单问题，则按优先级逐个提问。

下文中的 `AskUserQuestion` 引用仅为示例 — 在其他 runtime 中请使用本地等效工具。

## 步骤

### Step 0 — 校验物料目录

检查 `${TAPD_STORY_ROOT}/stories/<short_id>/` 是否存在且包含 `manifest.json`：

- 缺失 → 报错退出，提示先运行 `/tapd-story-breakdown <short-id>` 拉取物料，不得继续。

### Step 1 — 读取 manifest

读取 `manifest.json`，获取 `title`、`slug`、`url` 等字段，slug 是什么就用什么。

### Step 2 — 处理 feature branch

`slug` 是推荐分支名，任何分支创建/切换都必须先经用户确认：

1. `git branch --show-current` 获取当前分支，`git branch --list <slug>` 检查 slug 分支是否存在
2. 按以下情况处理：

| 情况 | 动作 |
| --- | --- |
| 当前分支 == slug | 无需动作，直接继续 |
| 当前分支 != slug，slug 分支不存在 | 询问："以当前分支为基点创建 `<slug>` 并切换？" 确认后执行 `git checkout -b <slug>` |
| 当前分支 != slug，slug 分支已存在 | 询问："切换到已有分支 `<slug>`？" 确认后执行 `git checkout <slug>` |
| 用户拒绝 | 不执行任何 git 操作，继续后续步骤；Step 4 摘要中标注"未切换到 slug 分支" |

### Step 3 — 加载需求内容

完整读取 `intake/prd.md`（唯一必读物料，其中已含每张图片的视觉分析文字与原型稿分析）。

图片文件不主动读取，开发中需要看图时再 Read `intake/images/` 下对应文件。

### Step 4 — 输出 handoff 摘要

以表格输出以下内容，输出后停止，等待用户指令：

- **需求**：`title` + TAPD `url`
- **分支**：当前分支名（未切换到 slug 分支时如实标注）
- **已加载**：prd.md
- **物料清单**：遍历 `${TAPD_STORY_ROOT}/stories/<short_id>/` 各目录，列出文件数、用途、何时读取

## 物料目录说明

```
${TAPD_STORY_ROOT}/stories/<short_id>/
├── manifest.json         # 需求元数据: id, short_id, title, slug, workspace_id, url, updated_at
├── intake/
│   ├── prd.md            # 工作副本: 清洗后的需求 + 图片本地引用 + 视觉/原型分析
│   ├── prd.raw.html      # TAPD API 原始富文本快照（排查清洗问题时查看）
│   ├── images/           # 富文本内嵌图片，开发中需要看图时按需 Read
│   ├── prototype/        # 全部 TAPD 附件原样保存（html 原型的分析已在 prd.md，原文按需查看）
│   └── ui/               # UI 稿，人工投放，按需查看
└── docs/                 # 技术文档，人工投放，按需查看
```

## 注意事项

- **不要跳过 Step 0**：物料目录不存在就明确报错，绝不代替用户拉取
- **分支确认**：slug 只是推荐分支名，任何 git 分支操作前必须经用户确认
