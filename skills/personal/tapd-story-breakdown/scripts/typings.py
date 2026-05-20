"""类型定义"""

from typing import TypedDict, List


class Story(TypedDict):
    """TAPD Story 基础信息"""

    id: str
    name: str
    description: str
    workitem_type_id: str  # 工作项类型 ID
    workspace_id: str  # 工作区 ID
    priority: str  # 优先级
    priority_label: str  # 优先级标签
    iteration_id: str  # 迭代 ID


class StoryData(TypedDict):
    """TAPD API 响应中的 Story 数据包装"""

    Story: Story


class StoryListResponse(TypedDict):
    """TAPD /stories 接口响应"""

    status: int
    data: List[StoryData]
    info: str


class Attachment(TypedDict):
    """TAPD /attachments 接口中的附件信息"""

    id: str
    type: str
    entry_id: str
    filename: str
    description: str | None
    content_type: str
    created: str
    workspace_id: str
    owner: str


class AttachmentData(TypedDict):
    """附件列表项"""

    Attachment: Attachment


class AttachmentListResponse(TypedDict):
    """TAPD /attachments 接口响应"""

    status: int
    data: List[AttachmentData]
    info: str


class ImageAttachment(TypedDict):
    """TAPD /files/get_image 接口响应中的附件信息"""

    type: str
    value: str
    workspace_id: str
    filename: str
    download_url: str


class ImageResponse(TypedDict):
    """TAPD /files/get_image 接口响应"""

    status: int
    data: dict
    info: str


class TaskInput(TypedDict):
    """JSON 文件中的任务输入格式

    用于 create_tasks.py 批量创建任务时的输入数据结构。
    """

    domain: str | None  # 业务域，如 "yos-web"，不存在时为 null
    dimension: str  # 任务维度，如 "C1", "C2", "C3"
    name: str  # 任务名称
    description: str  # 任务描述
    effort: float  # 任务工时（小时）


class UserInfo(TypedDict):
    """TAPD 用户信息"""

    id: str
    name: str
    email: str
    nick: str
    user_email: str


class UserInfoData(TypedDict):
    """TAPD /users/info 接口响应中的数据包装"""

    User: UserInfo


class UserInfoResponse(TypedDict):
    """TAPD /users/info 接口响应"""

    status: int
    data: UserInfo
    info: str
