#!/usr/bin/env python3
"""
TAPD 批量创建任务脚本

从 JSON 文件读取任务列表，批量在 TAPD 上创建任务并关联到指定 Story。
支持模拟模式（dry-run）预览创建结果。

Usage:
    python scripts/create_tasks.py --s <story_id> --f tasks/<story_id>.json
    python scripts/create_tasks.py --s <story_id> --f tasks/<story_id>.json --w <workspace_id>
    python scripts/create_tasks.py --s <story_id> --f tasks/<story_id>.json --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

from utils import load_env, to_long_id, make_request, print_json
from typings import TaskInput, UserInfoResponse, StoryListResponse


def create_tasks(
    story_id: str, workspace_id: str | None, json_file: str, dry_run: bool = False
) -> None:
    """
    批量创建 TAPD 任务

    Args:
        story_id: 父需求 ID
        workspace_id: 工作区 ID，可选。未提供时从 .env 读取
        json_file: 任务列表 JSON 文件路径（必须是绝对路径）
        dry_run: 模拟模式，不真实调用 API

    JSON 格式:
        [
            {
                "domain": "yos-web",      # 可选，业务域
                "dimension": "C1",        # 任务维度
                "name": "任务名称",
                "description": "任务描述",
                "effort": 2.5             # 工时（小时）
            }
        ]
    """
    # ========== Step 1: 参数校验 ==========
    json_path = Path(json_file)
    if not json_path.is_absolute():
        print(f"Error: JSON file path must be absolute, got: {json_file}")
        sys.exit(1)
    if not json_path.exists():
        print(f"Error: JSON file not found: {json_file}")
        sys.exit(1)

    # 读取并解析 JSON 文件
    with open(json_path) as f:
        tasks: list[TaskInput] = json.load(f)

    if not tasks:
        print("Error: No tasks to create.")
        sys.exit(1)

    # ========== Step 2: 加载配置 ==========
    # workspace_id 可选，未提供时从环境变量读取
    workspace_id = workspace_id or os.environ.get("TAPD_WORKSPACE_ID", "")
    if not workspace_id:
        print(
            "Error: workspace_id is required (provide via --workspace or configure in .env)"
        )
        sys.exit(1)

    # ========== Step 3: 获取当前用户信息 ==========
    # 获取创建人昵称（从接口获取）
    user_info: UserInfoResponse = make_request("GET", "/users/info")
    nick = user_info.get("data", {}).get("nick", "")

    # ========== Step 4: 获取父 Story 信息 ==========
    # 转换为长 ID
    long_story_id = to_long_id(story_id, workspace_id)

    story_info: StoryListResponse = make_request(
        "GET",
        "/stories",
        params={
            "id": long_story_id,
            "workspace_id": workspace_id,
            "fields": "id,workspace_id,priority,priority_label,iteration_id,custom_field_28",
            "limit": 1,
        },
    )

    if not story_info.get("data"):
        print(f"Error: Story not found with ID '{long_story_id}'")
        sys.exit(1)

    # 提取 story 基础信息，用于继承属性（优先级、迭代等）
    story = story_info["data"][0]["Story"]

    print(f"准备创建 {len(tasks)} 个任务，关联到 Story: {story['id']}")
    print("-" * 50)

    # ========== Step 5: 逐条创建任务 ==========
    success_count = 0
    for idx, task in enumerate(tasks, 1):
        # 构造任务数据
        task_data = {
            "workitem_type_id": "1140888836001000162",  # 任务类型
            "priority": story["priority"],  # 继承父需求优先级
            "priority_label": story["priority_label"],
            "iteration_id": story["iteration_id"],  # 继承父需求迭代
            "parent_id": story["id"],  # 关联父需求
            "workspace_id": story["workspace_id"],
            "name": _build_task_name(task),  # 任务名称
            "description": task["description"],  # 任务描述
            "effort": task["effort"],  # 预估工时
            "creator": nick,  # 创建人
            "owner": nick,  # 负责人
            "custom_field_28": story["custom_field_28"], # 自定义字段(项目名称)
            "custom_field_56": "前端研发",  # 自定义字段
        }

        print_json(task_data)

        if dry_run:
            # 模拟模式：仅打印预览
            task_id = f"mock_task_{idx}"
            print(f"[{idx}/{len(tasks)}] ✓ {task['name']} -> Task ID: {task_id}")
            print(f"     参数预览: name={task['name']}, effort={task['effort']}h")
            success_count += 1
        else:
            # 真实调用 TAPD API
            try:
                response = make_request("POST", "/stories", data=task_data)
                task_id = response.get("data", {}).get("Story", {}).get("id", "unknown")
                print(f"[{idx}/{len(tasks)}] ✓ {task['name']} -> Task ID: {task_id}")
                success_count += 1
            except Exception as e:
                print(f"[{idx}/{len(tasks)}] ✗ {task['name']} -> Error: {e}")

    # ========== Step 6: 输出统计 ==========
    print("-" * 50)
    print(f"创建完成: {success_count}/{len(tasks)} 成功")


def _build_task_name(task: TaskInput) -> str:
    """
    构造任务名称

    Args:
        task: 任务输入数据

    Returns:
        格式化的任务名称，如 "YOS-WEB - [C1] 任务名称" 或 "[C1] 任务名称"
    """
    if task.get("domain"):
        return f"{task['domain'].upper()} - [{task['dimension']}] {task['name']}"
    return f"[{task['dimension']}] {task['name']}"


if __name__ == "__main__":
    load_env()

    parser = argparse.ArgumentParser(description="创建任务")
    parser.add_argument("--story", "-s", required=True, help="Story ID")
    parser.add_argument("--workspace", "-w", required=False, help="Workspace ID")
    parser.add_argument(
        "--file", "-f", required=True, help="Story-Tasks JSON File Path"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="模拟模式，不真实调用 API"
    )

    args = parser.parse_args()

    create_tasks(args.story, args.workspace, args.file, args.dry_run)
