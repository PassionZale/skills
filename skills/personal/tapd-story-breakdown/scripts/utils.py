import os
import sys
import json
import base64
import zipfile
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Error: requests module not found. Install with: pip install requests")
    sys.exit(1)

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from prompts import VISION_PROMPT, PROTOTYPE_PROMPT


def load_env_file(p: str) -> dict[str, str]:
    env: dict[str, str] = {}
    try:
        with open(p, "r", encoding="utf8") as f:
            content = f.read()
    except OSError:
        return {}

    for line in content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("#"):
            continue
        idx = trimmed.find("=")
        if idx == -1:
            continue
        key = trimmed[:idx].strip()
        val = trimmed[idx + 1:].strip()
        if (val.startswith('"') and val.endswith('"')) or \
           (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        env[key] = val

    return env


def load_env() -> None:
    home = Path.home()
    cwd = Path.cwd()

    home_env = load_env_file(home / ".passionzale-skills" / ".env")
    cwd_env = load_env_file(cwd / ".passionzale-skills" / ".env")

    for k, v in home_env.items():
        if k not in os.environ:
            os.environ[k] = v

    for k, v in cwd_env.items():
        if k not in os.environ:
            os.environ[k] = v


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
    headers = {
        "Authorization": f"Bearer {os.environ['TAPD_ACCESS_TOKEN']}",
        "Content-Type": "application/json",
    }

    url = urljoin("https://api.tapd.cn/", endpoint)

    response = requests.request(
        method=method, url=url, headers=headers, params=params, json=data, timeout=30
    )

    response.raise_for_status()

    return response.json()


def format_json(data) -> str:
    """格式化 JSON 为字符串"""
    return json.dumps(data, ensure_ascii=False, indent=2)


def print_json(data):
    """美化打印 JSON"""
    print(format_json(data))


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


def to_short_id(long_id: str) -> str:
    """
    从长 ID 反推短 ID

    长 ID 结构为「2 位前缀 + workspace_id + 9 位补零段」，取末尾 9 位去前导零即为短 ID。
    长度不足 12 位的输入（不构成完整长 ID）原样去前导零返回。

    Args:
        long_id: 需求长 ID

    Returns:
        短 ID
    """
    long_id = str(long_id).strip()

    if long_id.isdigit() and len(long_id) >= 12:
        long_id = long_id[-9:]

    return long_id.lstrip("0") or "0"


def download_image(url: str) -> tuple[bytes, str] | None:
    """
    下载图片原始内容

    Args:
        url: 图片下载 URL

    Returns:
        (图片字节内容, Content-Type) 元组，失败时返回 None
    """
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content, resp.headers.get("Content-Type", "")
    except Exception as e:
        print(f"Warning: 图片下载失败（{url}）: {type(e).__name__}: {e}")
        return None


def _unique_path(path: Path) -> Path:
    """路径已存在时追加序号后缀（如 name-1.ext），避免同批附件互相覆盖"""
    if not path.exists():
        return path

    for i in range(1, 1000):
        candidate = path.with_name(f"{path.stem}-{i}{path.suffix}")
        if not candidate.exists():
            return candidate

    return path


def analyze_image_with_vision(image_data: bytes, mime_type: str = "image/png", context: str = "") -> str:
    """
    使用视觉模型解析图片内容

    Kimi 等视觉模型不接受远程图片 URL，图片以 base64 data URI 形式传入。

    Args:
        image_data: 图片二进制内容
        mime_type: 图片 MIME 类型，如 image/png；无法识别时回退 image/png
        context: 图片周围的文字上下文（可选）

    Returns:
        图片内容描述文本，失败或无 API Key 时返回空字符串
    """
    api_key = os.environ.get("ZAI_API_KEY", "")
    base_url = os.environ.get("ZAI_BASE_URL", "")
    model = os.environ.get("ZAI_VISION_MODEL", "")

    if not api_key:
        print("Warning: ZAI_API_KEY not set. Image analysis will be skipped.")
        return ""

    if not base_url:
        print("Warning: ZAI_BASE_URL not set. Image analysis will be skipped.")
        return ""

    if not model:
        print("Warning: ZAI_VISION_MODEL not set. Image analysis will be skipped.")
        return ""

    # 构建带上下文的 user prompt（按句子截断）
    context_text = ""
    if context:
        context_trimmed = context[:500]
        # 找最后一个句号/换行截断，避免截在句子中间
        cut = max(context_trimmed.rfind("。"), context_trimmed.rfind("\n"))
        if cut > 100:  # 截断点太靠前就不管了
            context_trimmed = context_trimmed[: cut + 1]
        context_text = f"\n\n图片所在段落的文字上下文：\n{context_trimmed}"

    user_text = f"这张图片来自产品需求文档。{context_text}\n\n请分析图片内容。"

    mime = (mime_type or "").split(";")[0].strip().lower() or "image/png"
    data_uri = f"data:{mime};base64,{base64.b64encode(image_data).decode('utf-8')}"

    # 配置重试策略
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,  # 1s, 2s, 4s
        status_forcelist=[429, 500, 502, 503],
        allowed_methods=["POST"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))

    try:
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        response = session.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": VISION_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {"type": "image_url", "image_url": {"url": data_uri}},
                        ],
                    },
                ],
                "thinking": {"type": "disabled"},
                "stream": False,
            },
            timeout=(5, 120),  # (connect_timeout, read_timeout)，base64 大图适当放宽
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Warning: 视觉模型分析失败: {type(e).__name__}: {e}")
        return ""
    finally:
        session.close()


def download_attachments(story_id: str, workspace_id: str, attach_dir: Path) -> list[Path]:
    """
    下载需求的全部附件到指定目录（不做类型过滤）

    zip 附件解压后删除原 zip，保留解压产物；其余类型原样保存。
    同批附件重名时自动追加序号后缀。

    Args:
        story_id: 需求长 ID
        workspace_id: 工作区 ID
        attach_dir: 附件保存目录（通常是 stories/<short_id>/intake/prototype/）

    Returns:
        解压后所有 HTML 文件的路径列表
    """
    from typings import AttachmentListResponse

    response: AttachmentListResponse = make_request(
        "GET",
        "/attachments",
        params={
            "workspace_id": workspace_id,
            "entry_id": story_id,
        },
    )

    attachments = [item["Attachment"] for item in response.get("data", [])]

    if not attachments:
        return []

    attach_dir.mkdir(parents=True, exist_ok=True)

    for att in attachments:
        download_url = make_request(
            "GET",
            "/attachments/down",
            params={
                "workspace_id": workspace_id,
                "id": att["id"],
            },
        )["data"]["Attachment"]["download_url"]

        local_file = _unique_path(attach_dir / (att.get("filename") or f"attachment-{att['id']}"))
        resp = requests.get(download_url, timeout=30)
        resp.raise_for_status()
        local_file.write_bytes(resp.content)

        # 解压 zip
        if att.get("content_type") == "application/zip":
            with zipfile.ZipFile(local_file, "r") as zf:
                zf.extractall(attach_dir)
            local_file.unlink()

    return sorted(attach_dir.glob("*.html"))


def analyze_html_with_llm(html_content: str, filename: str) -> str:
    """
    使用 GLM 文本模型分析 HTML 原型稿内容

    Args:
        html_content: HTML 文件内容
        filename: 文件名（用于日志）

    Returns:
        分析结果文本，失败或无 API Key 时返回空字符串
    """
    api_key = os.environ.get("ZAI_API_KEY", "")
    base_url = os.environ.get("ZAI_BASE_URL", "")
    model = os.environ.get("ZAI_BASE_MODEL", "")

    if not api_key:
        print("Warning: ZAI_API_KEY not set. HTML analysis will be skipped.")
        return ""

    if not base_url:
        print("Warning: ZAI_BASE_URL not set. HTML analysis will be skipped.")
        return ""

    if not model:
        print("Warning: ZAI_BASE_MODEL not set. HTML analysis will be skipped.")
        return ""

    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503],
        allowed_methods=["POST"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))

    try:
        api_url = f"{base_url.rstrip('/')}/chat/completions"
        response = session.post(
            api_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": PROTOTYPE_PROMPT},
                    {"role": "user", "content": html_content},
                ],
                "thinking": {"type": "disabled"},
                "stream": False,
            },
            timeout=(5, 60),
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Warning: HTML 原型稿分析失败（{filename}）: {type(e).__name__}: {e}")
        return ""
    finally:
        session.close()
