/**
 * routine-bot - GitLab MR / Jenkins 构建命令行工具
 *
 * 项目映射: ~/.passionzale-skills/routine-bot.json (模板见本 skill 目录下 config.example.json)
 */

import { execSync } from "child_process";
import { existsSync, readFileSync } from "fs";
import { homedir } from "os";
import { resolve } from "path";

// ─── Types ───────────────────────────────────────────────────────────────────

interface ProjectConfig {
  gitlabProjectId: number;
  targetBranches: Record<string, string>;
  jenkinsJobs: Record<string, string>;
}

interface RoutineBotConfig {
  projects: Record<string, ProjectConfig>;
}

interface GitlabMergeRequest {
  iid: number;
  project_id: number;
  title: string;
  state: string;
  web_url: string;
  source_branch: string;
  target_branch: string;
  merge_status: string;
  detailed_merge_status?: string; // 可选，GitLab 15.6+
  draft?: boolean;
  work_in_progress?: boolean; // 旧版本的草稿标识
  blocking_discussions_resolved?: boolean;
  pipeline?: {
    id: number;
    status: string;
  };
  approvals?: {
    approved: boolean;
    approvals_required: number;
    approvals_left: number;
  };
}

interface JenkinsJobList {
  jobs: { name: string }[];
}

// ─── Env Loading ─────────────────────────────────────────────────────────────

function loadEnvFile(p: string): Record<string, string> {
  if (!existsSync(p)) return {};
  const content = readFileSync(p, "utf-8");
  const env: Record<string, string> = {};
  for (const line of content.split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const idx = trimmed.indexOf("=");
    if (idx === -1) continue;
    const key = trimmed.slice(0, idx).trim();
    let val = trimmed.slice(idx + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    env[key] = val;
  }
  return env;
}

function loadEnv(): void {
  const home = homedir();
  const cwd = process.cwd();
  const homeEnv = loadEnvFile(resolve(home, ".passionzale-skills", ".env"));
  const cwdEnv = loadEnvFile(resolve(cwd, ".passionzale-skills", ".env"));
  for (const [k, v] of Object.entries(homeEnv)) {
    if (!(k in process.env)) process.env[k] = v;
  }
  for (const [k, v] of Object.entries(cwdEnv)) {
    if (!(k in process.env)) process.env[k] = v;
  }
}

// ─── Config Loading ──────────────────────────────────────────────────────────

const CONFIG_PATH = resolve(homedir(), ".passionzale-skills", "routine-bot.json");

function loadConfig(): RoutineBotConfig {
  if (!existsSync(CONFIG_PATH)) {
    throw new Error(
      `配置文件不存在: ${CONFIG_PATH}\n` +
        `请参考 skill 目录下的 config.example.json 创建，格式如下:\n` +
        `{\n` +
        `  "projects": {\n` +
        `    "<项目名，与 git remote 仓库名一致>": {\n` +
        `      "gitlabProjectId": <GitLab 项目 ID>,\n` +
        `      "targetBranches": { "dev": "...", "beta": "...", "uat": "...", "prod": "..." },\n` +
        `      "jenkinsJobs": { "dev": "...", "beta": "...", "uat": "...", "prod": "..." }\n` +
        `    }\n` +
        `  }\n` +
        `}`
    );
  }

  const config = JSON.parse(readFileSync(CONFIG_PATH, "utf-8")) as RoutineBotConfig;

  if (!config.projects || typeof config.projects !== "object") {
    throw new Error(`配置文件格式错误: ${CONFIG_PATH} 缺少 "projects" 字段`);
  }

  return config;
}

// ─── Git Helpers ─────────────────────────────────────────────────────────────

function execGit(command: string): string {
  try {
    return execSync(command, { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"] }).trim();
  } catch {
    throw new Error(`执行 git 命令失败: ${command}（请确认当前目录是一个 git 仓库）`);
  }
}

/** 从 git remote URL 中提取仓库名，如 https://host/group/repo.git -> repo */
function getRepoNameFromUrl(url: string): string {
  const match = url.match(/[/:]([^/:]+?)(?:\.git)?\/?$/);
  if (!match) {
    throw new Error(`无法从 remote URL 中解析仓库名: ${url}`);
  }
  return match[1];
}

/** 获取当前项目名（git remote origin 的仓库名） */
function getCurrentProjectName(): string {
  const url = execGit("git remote get-url origin");
  return getRepoNameFromUrl(url);
}

/** 获取当前分支名 */
function getCurrentBranch(): string {
  const branch = execGit("git branch --show-current");
  if (!branch) {
    throw new Error("无法获取当前分支（可能处于 detached HEAD 状态）");
  }
  return branch;
}

interface ProjectContext {
  projectName: string;
  projectId: number;
  targetBranch?: string;
  jobName?: string;
}

/**
 * 解析当前项目上下文:
 * - projectName 取自 git remote，可用 --project 覆盖
 * - env 合法性由该项目配置的 targetBranches / jenkinsJobs 键动态决定
 * - targetBranch / jobName 按 env 从配置映射（传入 env 时才解析）
 */
function resolveProject(
  config: RoutineBotConfig,
  options: { project?: string; env?: string },
  need: { targetBranch?: boolean; jobName?: boolean } = {}
): ProjectContext {
  const projectName = options.project || getCurrentProjectName();

  const project = config.projects[projectName];
  if (!project) {
    const available = Object.keys(config.projects).join(", ");
    throw new Error(
      `配置中不存在项目 "${projectName}"（来自 git remote 或 --project 参数）。\n` +
        `当前配置支持的项目: ${available}\n` +
        `请在 ${CONFIG_PATH} 中补充该项目。`
    );
  }

  if (!Number.isInteger(project.gitlabProjectId)) {
    throw new Error(`项目 "${projectName}" 的 gitlabProjectId 配置无效`);
  }

  // 需要 env 的命令（build/mr），env 必填且必须在该项目配置中定义
  const needsEnv = need.targetBranch === true || need.jobName === true;
  if (needsEnv && options.env === undefined) {
    throw new Error("缺少 --env 参数");
  }

  if (options.env !== undefined) {
    const definedEnvs = [
      ...new Set([
        ...Object.keys(project.targetBranches || {}),
        ...Object.keys(project.jenkinsJobs || {}),
      ]),
    ];
    if (!definedEnvs.includes(options.env)) {
      throw new Error(
        `项目 "${projectName}" 的配置中不存在环境 "${options.env}"。\n` +
          `可用环境: ${definedEnvs.join(", ")}\n` +
          `如需新增环境，请在 ${CONFIG_PATH} 中补充。`
      );
    }
  }

  if (!Number.isInteger(project.gitlabProjectId)) {
    throw new Error(`项目 "${projectName}" 的 gitlabProjectId 配置无效`);
  }

  const ctx: ProjectContext = {
    projectName,
    projectId: project.gitlabProjectId,
  };

  if (need.targetBranch) {
    ctx.targetBranch = project.targetBranches?.[options.env!];
    if (!ctx.targetBranch) {
      throw new Error(`项目 "${projectName}" 缺少 targetBranches.${options.env} 配置`);
    }
  }

  if (need.jobName) {
    ctx.jobName = project.jenkinsJobs?.[options.env!];
    if (!ctx.jobName) {
      throw new Error(`项目 "${projectName}" 缺少 jenkinsJobs.${options.env} 配置`);
    }
  }

  return ctx;
}

// ─── HTTP Clients ────────────────────────────────────────────────────────────

async function parseResponseBody(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

async function gitlabRequest<T>(
  method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH",
  endpoint: string,
  body?: unknown
): Promise<T> {
  const baseUrl = process.env.GITLAB_BASE_URL;
  const accessToken = process.env.GITLAB_ACCESS_TOKEN;

  if (!baseUrl) {
    throw new Error(
      "GITLAB_BASE_URL 未设置。请在 ~/.passionzale-skills/.env 中配置。"
    );
  }
  if (!accessToken) {
    throw new Error(
      "GITLAB_ACCESS_TOKEN 未设置。请在 ~/.passionzale-skills/.env 中配置。"
    );
  }

  const response = await fetch(`${baseUrl}/api/v4/${endpoint}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "PRIVATE-TOKEN": accessToken,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const responseBody = await parseResponseBody(response);

  if (!response.ok) {
    throw new Error(
      `GitLab API 请求失败 (${response.status} ${method} ${endpoint}): ${JSON.stringify(responseBody)}`
    );
  }

  return responseBody as T;
}

async function jenkinsRequest<T>(
  method: "GET" | "POST",
  endpoint: string
): Promise<T> {
  const baseUrl = process.env.JENKINS_BASE_URL;
  const username = process.env.JENKINS_USERNAME;
  const accessToken = process.env.JENKINS_ACCESS_TOKEN;

  if (!baseUrl) {
    throw new Error(
      "JENKINS_BASE_URL 未设置。请在 ~/.passionzale-skills/.env 中配置。"
    );
  }
  if (!username) {
    throw new Error(
      "JENKINS_USERNAME 未设置。请在 ~/.passionzale-skills/.env 中配置。"
    );
  }
  if (!accessToken) {
    throw new Error(
      "JENKINS_ACCESS_TOKEN 未设置。请在 ~/.passionzale-skills/.env 中配置。"
    );
  }

  const response = await fetch(`${baseUrl}/${endpoint}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      Authorization:
        "Basic " + Buffer.from(`${username}:${accessToken}`).toString("base64"),
    },
  });

  const responseBody = await parseResponseBody(response);

  if (!response.ok) {
    throw new Error(
      `Jenkins API 请求失败 (${response.status} ${method} ${endpoint}): ${JSON.stringify(responseBody)}`
    );
  }

  return responseBody as T;
}

// ─── Mergeability ────────────────────────────────────────────────────────────

async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function checkMergeability(mr: GitlabMergeRequest): {
  canMerge: boolean;
  shouldWait: boolean;
  reason: string;
} {
  // 首先检查 MR 是否处于开放状态
  if (mr.state !== "opened") {
    return { canMerge: false, shouldWait: false, reason: `Merge request is ${mr.state}` };
  }

  // 检查是否为草稿状态
  if (mr.draft || mr.work_in_progress) {
    return { canMerge: false, shouldWait: false, reason: "Cannot merge draft merge request" };
  }

  // 如果支持 detailed_merge_status (GitLab 15.6+)，优先使用
  if (mr.detailed_merge_status) {
    switch (mr.detailed_merge_status) {
      case "mergeable":
        return { canMerge: true, shouldWait: false, reason: "" };

      case "ci_still_running":
      case "checking":
        return {
          canMerge: false,
          shouldWait: true,
          reason: `CI/checks in progress: ${mr.detailed_merge_status}`,
        };

      case "blocked_status":
        return {
          canMerge: false,
          shouldWait: false,
          reason: "Merge request is blocked by branch protection rules",
        };

      case "broken_status":
        return {
          canMerge: false,
          shouldWait: false,
          reason: "Merge request has merge conflicts",
        };

      case "ci_must_pass":
        return {
          canMerge: false,
          shouldWait: false,
          reason: "CI pipeline must pass before merging",
        };

      case "discussions_not_resolved":
        return {
          canMerge: false,
          shouldWait: false,
          reason: "All discussions must be resolved before merging",
        };

      case "not_approved":
        return {
          canMerge: false,
          shouldWait: false,
          reason: "Merge request requires approval",
        };

      case "policies_denied":
        return {
          canMerge: false,
          shouldWait: false,
          reason: "Merge blocked by security policies",
        };
    }
  }

  // 降级到基础的 merge_status 检查 (兼容旧版本)
  switch (mr.merge_status) {
    case "cannot_be_merged":
      return {
        canMerge: false,
        shouldWait: false,
        reason: "Merge request cannot be merged (likely has conflicts)",
      };

    case "unchecked":
      return {
        canMerge: false,
        shouldWait: true,
        reason: "Merge status is being checked",
      };
  }

  // 检查 CI 流水线状态
  if (mr.pipeline) {
    const pipelineStatus = mr.pipeline.status;
    if (["pending", "running"].includes(pipelineStatus)) {
      return {
        canMerge: false,
        shouldWait: true,
        reason: `Pipeline is ${pipelineStatus}`,
      };
    }

    if (["failed", "canceled", "skipped"].includes(pipelineStatus)) {
      return {
        canMerge: false,
        shouldWait: false,
        reason: `Pipeline ${pipelineStatus}`,
      };
    }
  }

  // 检查讨论是否已解决
  if (mr.blocking_discussions_resolved === false) {
    return {
      canMerge: false,
      shouldWait: false,
      reason: "All discussions must be resolved before merging",
    };
  }

  // 检查审批状态
  if (mr.approvals && !mr.approvals.approved) {
    if (mr.approvals.approvals_left > 0) {
      return {
        canMerge: false,
        shouldWait: false,
        reason: `Merge request needs ${mr.approvals.approvals_left} more approval(s)`,
      };
    }
  }

  // 如果通过了所有检查，认为可以合并
  return { canMerge: true, shouldWait: false, reason: "" };
}

/** 轮询等待 MR 变为可合并状态（2 秒一次，2 分钟超时） */
async function waitForMergeability(projectId: number, mrIid: number): Promise<void> {
  const startTime = Date.now();
  const pollInterval = 2000; // 2秒轮询一次
  const maxWaitTime = 2 * 60 * 1000; // 2分钟超时

  while (Date.now() - startTime < maxWaitTime) {
    const mr = await gitlabRequest<GitlabMergeRequest>(
      "GET",
      `projects/${projectId}/merge_requests/${mrIid}`
    );

    const check = checkMergeability(mr);

    if (check.canMerge) {
      return;
    }

    if (check.shouldWait) {
      console.error(`Waiting... ${check.reason}`);
      await delay(pollInterval);
      continue;
    }

    throw new Error(check.reason);
  }

  throw new Error(
    `Timeout waiting for merge request to become mergeable after ${maxWaitTime}ms`
  );
}

// ─── Commands ────────────────────────────────────────────────────────────────

/** 列出 Jenkins Job */
async function cmdJobs(): Promise<unknown> {
  const { jobs } = await jenkinsRequest<JenkinsJobList>("GET", "api/json?tree=jobs[name]");
  return jobs;
}

/** 触发 Jenkins Job 构建 */
async function cmdBuild(config: RoutineBotConfig, options: { env?: string; project?: string }) {
  const ctx = resolveProject(config, options, { jobName: true });

  await jenkinsRequest<unknown>("POST", `job/${ctx.jobName}/build`);

  const baseUrl = process.env.JENKINS_BASE_URL;
  return {
    job_name: ctx.jobName,
    detail_url: `${baseUrl}/job/${ctx.jobName}`,
  };
}

/** 创建 Merge Request */
async function cmdCreateMr(config: RoutineBotConfig, options: { env?: string; project?: string }) {
  const ctx = resolveProject(config, options, { targetBranch: true });
  const sourceBranch = getCurrentBranch();

  const mr = await gitlabRequest<GitlabMergeRequest>(
    "POST",
    `projects/${ctx.projectId}/merge_requests`,
    {
      source_branch: sourceBranch,
      target_branch: ctx.targetBranch,
      title: `Merge ${sourceBranch} into ${ctx.targetBranch} Via routine-bot`,
    }
  );

  return {
    project_id: mr.project_id,
    iid: mr.iid,
    web_url: mr.web_url,
    source_branch: mr.source_branch,
    target_branch: mr.target_branch,
  };
}

/** 等待可合并后合并 Merge Request */
async function cmdMergeMr(
  config: RoutineBotConfig,
  options: { iid: number; project?: string }
) {
  const ctx = resolveProject(config, options);

  // === 1.等待 MR 变为可合并状态 ===
  await waitForMergeability(ctx.projectId, options.iid);

  // === 2.合并 MR ===
  const mergedMr = await gitlabRequest<GitlabMergeRequest>(
    "PUT",
    `projects/${ctx.projectId}/merge_requests/${options.iid}/merge`
  );

  return {
    web_url: mergedMr.web_url,
  };
}

// ─── CLI ─────────────────────────────────────────────────────────────────────

function usage(): string {
  return `routine-bot - GitLab MR / Jenkins 构建命令行工具

用法: bun main.ts <command> [options]

Commands:
  jobs                          列出 Jenkins Jobs
  build    --env <env>          触发 Jenkins Job 构建
  mr       --env <env>          创建 Merge Request（当前分支 -> 目标分支）
  merge    --iid <iid>          等待 MR 可合并后合并（2s 轮询，2min 超时）

Options:
  --env <env>        环境名（取值由 ~/.passionzale-skills/routine-bot.json 中该项目的配置键决定）
  --iid <number>     Merge Request 的 IID（merge 必需）
  --project <name>   项目名覆盖（默认从 git remote origin 自动识别）
  -h, --help         显示帮助

配置:
  项目映射: ~/.passionzale-skills/routine-bot.json
  环境变量: ~/.passionzale-skills/.env
    GITLAB_BASE_URL, GITLAB_ACCESS_TOKEN,
    JENKINS_BASE_URL, JENKINS_USERNAME, JENKINS_ACCESS_TOKEN`;
}

interface Options {
  env?: string;
  iid?: number;
  project?: string;
}

function parseArgs(argv: string[]): { command: string | null; options: Options } {
  const command = argv[0] || null;
  const options: Options = {};

  for (let i = 1; i < argv.length; i++) {
    const arg = argv[i];
    switch (arg) {
      case "--env":
        options.env = argv[++i];
        break;
      case "--iid":
        options.iid = Number(argv[++i]);
        break;
      case "--project":
        options.project = argv[++i];
        break;
      default:
        throw new Error(`未知参数: ${arg}\n\n${usage()}`);
    }
  }

  return { command, options };
}

function requireIid(options: Options): number {
  if (!options.iid || !Number.isInteger(options.iid) || options.iid <= 0) {
    throw new Error(`--iid 必须为正整数，当前值: ${options.iid ?? "(未提供)"}`);
  }
  return options.iid;
}

async function main(): Promise<void> {
  loadEnv();

  const argv = process.argv.slice(2);

  // --help 不需要加载配置
  if (argv.length === 0 || argv.includes("-h") || argv.includes("--help")) {
    console.log(usage());
    return;
  }

  const { command, options } = parseArgs(argv);

  switch (command) {
    case "jobs": {
      const data = await cmdJobs();
      console.log(JSON.stringify({ success: true, data }, null, 2));
      return;
    }

    case "build": {
      const config = loadConfig();
      const data = await cmdBuild(config, { env: options.env, project: options.project });
      console.log(JSON.stringify({ success: true, data }, null, 2));
      return;
    }

    case "mr": {
      const config = loadConfig();
      const data = await cmdCreateMr(config, { env: options.env, project: options.project });
      console.log(JSON.stringify({ success: true, data }, null, 2));
      return;
    }

    case "merge": {
      const iid = requireIid(options);
      const config = loadConfig();
      const data = await cmdMergeMr(config, { iid, project: options.project });
      console.log(JSON.stringify({ success: true, data }, null, 2));
      return;
    }

    default:
      throw new Error(`未知命令: ${command}\n\n${usage()}`);
  }
}

main().catch((error) => {
  console.error(JSON.stringify({ success: false, error: (error as Error).message }, null, 2));
  process.exit(1);
});
