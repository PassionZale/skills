# glmv-image-analyzer

基于智谱视觉模型（GLM-4V）的图片分析 CLI，封装了 7 种专用分析工具，供 skill 脚本化调用。

## 环境变量

从 `~/.passionzale-skills/.env` 和 `./.passionzale-skills/.env` 加载：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ZAI_API_KEY` | API Key（必填） | — |
| `ZAI_BASE_URL` | API Endpoint | `https://open.bigmodel.cn/api/paas/v4/` |
| `ZAI_VISION_MODEL` | 视觉模型 | `glm-4.6v` |

## 工具列表

### 通用分析

```bash
bun scripts/main.ts analyze --image_source <path|url> --prompt <text>
```

### OCR 文字提取

```bash
bun scripts/main.ts ocr --image_source <path|url> --prompt <text> [--programming_language <lang>]
```

### 错误诊断

```bash
bun scripts/main.ts error --image_source <path|url> --prompt <text> [--context <text>]
```

### 技术图表分析

```bash
bun scripts/main.ts diagram --image_source <path|url> --prompt <text> [--diagram_type <type>]
```

### 数据可视化分析

```bash
bun scripts/main.ts data-viz --image_source <path|url> --prompt <text> [--analysis_focus <focus>]
```

### UI 转 Artifact

```bash
bun scripts/main.ts ui-to-code --image_source <path|url> --output_type <code|prompt|spec|description> --prompt <text>
```

### UI 对比检查

```bash
bun scripts/main.ts ui-diff --expected_image_source <path|url> --actual_image_source <path|url> --prompt <text>
```

## 参数说明

- `image_source` 支持本地文件路径（绝对/相对）和 URL，本地文件自动 base64 编码
- 支持的图片格式：`.jpg`、`.jpeg`、`.png`，最大 5MB
- 所有工具名和参数名与 [zai-mcp-server](https://www.npmjs.com/package/@z_ai/mcp-server) 保持一致

## 输出格式

成功时通过 stdout 输出 JSON：

```json
{"success": true, "data": "分析结果文本"}
```

失败时通过 stderr 输出 JSON，退出码为 1：

```json
{"success": false, "error": "错误信息"}
```

## 运行时

依赖 [Bun](https://bun.sh/) 运行时：

```bash
bun scripts/main.ts <tool> [options]
# 或
npx -y bun scripts/main.ts <tool> [options]
```

查看帮助：

```bash
bun scripts/main.ts help
```
