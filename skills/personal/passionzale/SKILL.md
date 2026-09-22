---
name: passionzale
description: 当需要触发 Jenkins Job 构建、创建 GitLab Merge Request、合并 Merge Request，或执行部署流程时使用此技能。当用户说"构建"、"发 MR"、"创建合并请求"、"合并"、"部署"、"发版"、"上线"等时触发。
disable-model-invocation: true
---

# Passionzale

通过 CLI 脚本操作 GitLab Merge Request 和 Jenkins 构建。

| 子命令 | 用途 |
|--------|------|
| `jobs` | 列出 Jenkins Jobs |
| `build` | 触发 Jenkins Job 构建 |
| `mr` | 创建 Merge Request |
| `merge` | 等待可合并后合并 MR |

## 脚本目录

**重要**：所有脚本均位于本技能的 `scripts/` 子目录中。

**Agent 执行说明**：

1. 确定本 `SKILL.md` 文件所在目录路径，记为 `{baseDir}`
2. 脚本路径 = `{baseDir}/scripts/main.ts`
3. 将本文档中所有 `{baseDir}` 替换为实际路径
4. 解析 `${BUN_X}` 运行时：若已安装 `bun` → 使用 `bun`；若有 `npx` → 使用 `npx -y bun`；否则提示用户安装 `bun`

## 使用方式

```bash
${BUN_X} {baseDir}/scripts/main.ts <command> [options]
```

**查看帮助**: `${BUN_X} {baseDir}/scripts/main.ts --help`

## 命令与参数

| 命令 | 必需参数 | 说明 |
|------|---------|------|
| `jobs` | 无 | 列出 Jenkins Jobs（只读） |
| `build --env <env>` | `--env` | 触发 Jenkins Job 构建 |
| `mr` | `--env` 或 `--target-branch`（至少其一） | 创建 MR（源分支默认当前分支，目标分支默认环境映射） |
| `merge --iid <iid>` | `--iid` | 等待 MR 可合并（2s 轮询，2min 超时）后合并 |

可选参数：

- `--env <env>`：环境名，**单次调用只支持一个环境**；多环境需求请按顺序多次调用。可用取值由 `~/.passionzale-skills/passionzale.json` 中该项目配置的键决定，配置是什么就是什么，未配置的环境会报错并列出可用值
- `--source-branch <branch>`：MR 的源分支，默认取当前检出的分支
- `--target-branch <branch>`：MR 的目标分支，**显式指定优先于 `--env` 的环境映射**；与 `--env` 至少提供其一
- `--project <name>`：项目名覆盖。默认脚本会从 `git remote get-url origin` 自动识别仓库名，一般无需手动指定

## 项目与环境映射

项目配置（GitLab projectId、env → 目标分支、env → Jenkins Job）位于:

```
~/.passionzale-skills/passionzale.json
```

模板见本技能目录下的 `config.example.json`。若脚本报错"配置文件不存在"或"配置中不存在项目"，请引导用户参照模板补全配置。

字段说明：

- `targetBranches.<env>`：该环境对应的 GitLab 目标分支
- `jenkinsJobs.<env>`：该环境对应的 Jenkins Job 名称
- env 的集合完全由配置决定，不固定

## 部署编排

用户要求"部署/发版到某环境"时，按以下顺序执行（每个环境一条完整管道，多环境依次重复）：

1. **确定环境**：确认目标 env。用户未指定时，先读取 `~/.passionzale-skills/passionzale.json` 中当前项目配置的环境键，让用户从中选择
2. **检查工作区**：执行 `git status --porcelain`，若有未提交的代码，**中止流程**并引导用户先提交（如使用 git-commit 技能）或暂存
3. **创建 MR**：`mr --env <env>`，从输出的 JSON 中记下 `data.iid`
4. **合并 MR**：`merge --iid <上一步的 iid>`（脚本内部会等待 CI/检查通过后再合并）
5. **触发构建**：`build --env <env>`

任何一步失败（stderr 输出 `"success": false`）都应停止并向用户报告错误信息，不要继续后续步骤。

## 输出格式

成功时通过 stdout 输出 JSON：

```json
{ "success": true, "data": { "...": "..." } }
```

失败时通过 stderr 输出 JSON，退出码为 1：

```json
{ "success": false, "error": "错误信息" }
```

等待合并时可合并性进度输出在 stderr（非 JSON），属正常现象。
