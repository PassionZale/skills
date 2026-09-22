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
