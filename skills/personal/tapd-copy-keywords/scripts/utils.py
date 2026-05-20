import subprocess
import os
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Error: requests module not found. Install with: pip install requests")

from typings import EnvConfig


def run_command(cmd: str) -> dict:
    """Run a shell command and return result."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=False
        )
        return {
            "success": result.returncode == 0,
            "output": result.stdout.strip(),
            "error": result.stderr.strip(),
        }
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}


def get_git_repo_name() -> str | None:
    """Get the git repository name."""
    result = run_command("git rev-parse --show-toplevel")
    if not result["success"]:
        return None
    return os.path.basename(result["output"])


def get_project_name() -> str | None:
    """Get project name from git repo or current directory."""
    repo_name = get_git_repo_name() or os.path.basename(os.getcwd())
    return repo_name

def load_env() -> EnvConfig:
    """
    从 skill 目录的 .env 文件加载环境配置

    Returns:
        包含 TAPD_WORKSPACE_ID、TAPD_ACCESS_TOKEN 的配置字典
    """
    skill_dir = Path(__file__).parent.parent
    env_file = skill_dir / ".env"

    if not env_file.exists():
        print(f"Error: .env file not found at {env_file}")
        print("Please copy .env.example to .env and configure your settings.")
        sys.exit(1)

    config = {}

    with open(env_file) as lines:
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    return config    


def make_request(
    method: str,
    endpoint: str,
    params: Optional[dict] = None,
    data: Optional[dict] = None,
) -> Dict:
    """
    向 TAPD API 发送 HTTP 请求

    Args:
        method: HTTP 方法（GET、POST、PUT、DELETE 等）
        endpoint: API 端点路径（如 /stories）
        params: URL 查询参数
        data: 请求体数据（JSON 格式）

    Returns:
        API 响应的 JSON 数据

    Raises:
        requests.HTTPError: 请求失败时抛出异常
    """
    config = load_env()

    headers = {
        "Authorization": f"Bearer {config['TAPD_ACCESS_TOKEN']}",
        "Content-Type": "application/json",
    }

    url = urljoin("https://api.tapd.cn/", endpoint)

    response = requests.request(
        method=method, url=url, headers=headers, params=params, json=data, timeout=30
    )

    response.raise_for_status()

    return response.json()


def to_long_id(story_id: str, workspace_id: str, is_cloud: bool = True) -> str:
    """
    将短 story_id 转换为长 ID

    Args:
        story_id: 原始 story_id
        workspace_id: 工作区 ID
        is_cloud: 是否为云环境，默认 True

    Returns:
        转换后的 story_id（如果不是短 ID，原样返回）
    """
    story_id = str(story_id).strip()

    # 如果是纯数字且 ≤ 9 位，视为短 ID
    if story_id.isdigit() and len(story_id) <= 9:
        pre_id = "11" if is_cloud else "10"
        padded_id = story_id.zfill(9)
        return f"{pre_id}{workspace_id}{padded_id}"

    return story_id
