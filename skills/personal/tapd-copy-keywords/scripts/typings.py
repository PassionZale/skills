"""类型定义"""

from typing import TypedDict


class EnvConfig(TypedDict):
    """环境配置"""

    TAPD_WORKSPACE_ID: str
    TAPD_ACCESS_TOKEN: str
