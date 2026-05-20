import argparse
import sys
from typing import Optional
from utils import load_env, to_long_id, make_request


def get_scm_copy_keywords(story_id: str, workspace_id: Optional[str] = None) -> None:
    config = load_env()
    workspace_id = workspace_id or config["TAPD_WORKSPACE_ID"]

    if not workspace_id:
        print("Error: the following arguments are required: --workspace")
        sys.exit(1)

    long_story_id = to_long_id(story_id, workspace_id)

    response = make_request(
        "GET",
        "/svn_commits/get_scm_copy_keywords",
        params={
            "workspace_id": workspace_id,
            "object_id": long_story_id,
            "type": "story",
        },
    )

    print(f"源码关键字: {response.get('data')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取需求详情")
    parser.add_argument("--story", "-s", required=True, help="Story ID")
    parser.add_argument("--workspace", "-w", required=False, help="Workspace ID")

    args = parser.parse_args()

    get_scm_copy_keywords(args.story, args.workspace)
