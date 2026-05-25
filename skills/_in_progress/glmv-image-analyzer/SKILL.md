---
name: glmv-image-analyzer
description: 支持多种图像格式的智能分析和内容理解. 当用户说 "分析图片", "识别图片" 时触发.
---

# Image Analyzer (GLM SDK)

基于智谱官方 SDK 的图片分析和理解.

## 用户输入工具

当本技能需要向用户提问时，按以下优先级选择工具：

1. **优先使用内置用户输入工具**：优先调用当前 Agent 运行时暴露的工具，例如 `AskUserQuestion`、`request_user_input`、`clarify`、`ask_user` 或其他同等功能的工具。
2. **备选方案**：若不存在此类工具，则输出编号的纯文本消息，要求用户回复对应的编号或答案。
3. **批量处理**：若工具支持单次调用包含多个问题，则将所有相关问题合并为一次调用；若仅支持单问题，则按优先顺序逐一提问。

下方出现的 `AskUserQuestion` 仅为示例，在其他运行时中请替换为对应的本地工具。

## 脚本目录

**重要**：所有脚本均位于本技能的 `scripts/` 子目录中。

**Agent 执行说明**：

1. 确定本 `SKILL.md` 文件所在目录路径，记为 `${BASE_DIR}`
2. 脚本路径 = `{BASE_DIR}/scripts/<script_name>.ts`
3. 将本文档中所有 `${BASE_DIR}` 替换为实际路径
4. 解析 `${BUN}` 运行时：若已安装 `bun` → 使用 `bun`；若有 `npx` → 使用 `npx -y bun`；否则提示用户安装 bun

**脚本说明**：
| 脚本 | 用途 |
|------|------|
| `scripts/main.ts` | 主脚本 |

##