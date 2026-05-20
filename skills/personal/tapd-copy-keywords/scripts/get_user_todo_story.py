import argparse
import json
import os
import sys
from typing import Optional
from utils import load_env, make_request, get_project_name


def filter_stories(stories_data: dict) -> list:
    """
    过滤 story 列表，只保留符合条件的项目

    过滤条件：
    1. workitem_type_id 为 '1140888836001000162'
    2. story name 以当前项目名（大写）开头

    Args:
        stories_data: TAPD API 返回的数据结构

    Returns:
        过滤后的 story 列表
    """
    project_name = get_project_name()
    if not project_name:
        return []

    # 转为大写作为前缀（例如 foo-bar -> FOO-BAR）
    project_prefix = project_name.upper()
    target_type_id = "1140888836001000162"
    filtered = []

    for item in stories_data.get("data", []):
        story = item.get("Story", {})
        workitem_type_id = story.get("workitem_type_id")
        name = story.get("name", "")

        if workitem_type_id != target_type_id:
            continue

        if name.startswith(project_prefix):
            filtered.append(
                {
                    "story_id": story["id"],
                    "story_name": story["name"],
                    "workspace_id": story["workspace_id"],
                }
            )

    return filtered


def get_user_todo_story(workspace_id: Optional[str] = None) -> None:
    workspace_id = workspace_id or os.environ.get("TAPD_WORKSPACE_ID", "")

    if not workspace_id:
        print("Error: the following arguments are required: --workspace")
        sys.exit(1)

    response = make_request(
        "GET",
        "/user_oauth/get_user_todo_story",
        params={
            "workspace_id": workspace_id,
            "fields": "id,workspace_id,workitem_type_id,name",
            "order": "created asc",
            "limit": 200,
        },
    )

    filtered = filter_stories(response)
    print(f"共 {len(filtered)} 个符合条件的 story：\n")
    print(json.dumps(filtered, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    load_env()

    parser = argparse.ArgumentParser(description="获取当前用户的待办 story 列表")
    parser.add_argument("--workspace", "-w", required=False, help="Workspace ID")

    args = parser.parse_args()

    get_user_todo_story(args.workspace)
