#!/usr/bin/env python3

"""
从 TAPD 获取需求（Story）详情脚本

功能：
- 支持短 ID 或长 ID 查询
- 并发调用视觉模型分析所有图片
- 将图片替换为结构化文本说明
- 输出纯文本格式供 LLM 理解
"""

import argparse
import os
import sys
import concurrent.futures
from pathlib import Path
from typing import Optional
try:
    from bs4 import BeautifulSoup, NavigableString
except ImportError:
    print("Error: bs4 module not found. Install with: pip install bs4")
    sys.exit(1)

try:
    from markdownify import markdownify as md
except ImportError:
    print("Error: markdownify module not found. Install with: pip install markdownify")
    sys.exit(1)
from utils import (
    load_env,
    make_request,
    to_long_id,
    analyze_image_with_vision,
    download_attachments,
    analyze_html_with_llm,
)
from typings import StoryListResponse, ImageResponse


# =============================================================================
# 图片处理函数
# =============================================================================


def get_tapd_image(src: str, workspace_id: str) -> tuple[str, str]:
    """
    获取图片下载 URL（不含视觉模型调用）

    Args:
        src: 图片 src 路径（可能是 /tfl/ 相对路径或完整 URL）
        workspace_id: TAPD 工作区 ID

    Returns:
        (original_src, download_url) 元组
    """
    url = src

    # 如果是 /tfl/ 路径，调用 TAPD API 获取下载 URL
    if src.startswith("/tfl/"):
        response: ImageResponse = make_request(
            "GET",
            "/files/get_image",
            params={
                "workspace_id": workspace_id,
                "image_path": src,
            },
        )
        url = response["data"]["Attachment"]["download_url"]

    return (src, url)


def get_surrounding_text(img_tag, char_limit: int = 200) -> str:
    """
    提取图片标签周围的文字上下文

    Args:
        img_tag: BeautifulSoup img 标签对象
        char_limit: 前后各自取多少字符，默认 200

    Returns:
        图片周围的文字上下文
    """
    texts = []

    # 往前找：兄弟节点
    for sibling in img_tag.previous_siblings:
        if isinstance(sibling, NavigableString):
            texts.insert(0, sibling.strip())
        elif sibling.name in ("p", "div", "span", "li", "h1", "h2", "h3"):
            texts.insert(0, sibling.get_text(strip=True))
        if sum(len(t) for t in texts) >= char_limit:
            break

    before = " ".join(t for t in texts if t)[-char_limit:]

    # 往后找：兄弟节点
    texts = []
    for sibling in img_tag.next_siblings:
        if isinstance(sibling, NavigableString):
            texts.append(sibling.strip())
        elif sibling.name in ("p", "div", "span", "li", "h1", "h2", "h3"):
            texts.append(sibling.get_text(strip=True))
        if sum(len(t) for t in texts) >= char_limit:
            break

    after = " ".join(t for t in texts if t)[:char_limit]

    return f"{before} [图片在此] {after}".strip()


def enrich_description_with_vision(html: str, workspace_id: str) -> str:
    """
    使用视觉模型分析图片并替换为结构化文本

    Args:
        html: 原始 description HTML
        workspace_id: TAPD 工作区 ID

    Returns:
        替换图片后的纯文本 description
    """
    if not html:
        return ""

    # 1. description (html) 输入
    print(f"[1/5] 接收需求描述: ({len(html)} 字符)")

    soup = BeautifulSoup(html, "html.parser")

    # 2. 提取所有 img src
    img_info_list: list[tuple] = []  # [(img_tag, original_src, download_url), ...]
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith("data:"):
            continue
        original_src, download_url = get_tapd_image(src, workspace_id)
        img_info_list.append((img, original_src, download_url))

    if not img_info_list:
        # 无图片，直接转 Markdown
        print("[2/5] 未检测到图片，跳过视觉分析")
        return md(str(soup))

    print(f"[2/5] 检测到 {len(img_info_list)} 张图片，提取下载 URL 完成")

    # 3. 并发调用视觉模型分析每张图
    vision_results: dict[str, str] = {}  # {download_url: analysis_text}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # 构建 {url: context} 映射
        url_to_context: dict[str, str] = {}
        for img_tag, _, download_url in img_info_list:
            url_to_context[download_url] = get_surrounding_text(img_tag)

        print(f"[3/5] 并发调用视觉模型分析 {len(img_info_list)} 张图片...")

        # 提交任务时传入 context
        future_to_url = {
            executor.submit(
                analyze_image_with_vision, url, url_to_context.get(url, "")
            ): url
            for _, _, url in img_info_list
        }
        completed = 0
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                completed += 1
                print(f"      进度: {completed}/{len(img_info_list)}")
                if result:
                    vision_results[url] = result
            except Exception:
                pass

    # 4. 将分析结果替换回 html
    print("[4/5] 将分析结果替换回需求描述")
    for img_tag, _, download_url in img_info_list:
        analysis = vision_results.get(download_url, "")

        if analysis:
            placeholder = soup.new_tag("div")
            placeholder.string = f"[图片内容说明]\n{analysis}\n[/图片内容说明]"
            img_tag.replace_with(placeholder)
        else:
            img_tag.decompose()

    # 5. html 转 Markdown
    print("[5/5] 需求描述解析完成")
    return md(str(soup))


# =============================================================================
# 附件处理函数
# =============================================================================


def parse_attachments(story_id: str, workspace_id: str) -> str:
    """
    下载并分析需求附件，返回附件分析文本

    Args:
        story_id: 需求长 ID
        workspace_id: 工作区 ID

    Returns:
        附件分析文本，无附件时返回空字符串
    """
    print("[1/2] 下载原型附件...")
    html_files = download_attachments(story_id, workspace_id)

    if not html_files:
        print("[2/2] 未检测到 HTML 原型附件，跳过附件分析")
        return ""

    print(f"[2/2] 检测到 {len(html_files)} 个 HTML 原型文件，调用文本模型分析...")
    results: list[tuple[str, str]] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_name = {
            executor.submit(
                analyze_html_with_llm, f.read_text("utf-8"), f.name
            ): f.name
            for f in html_files
        }
        completed = 0
        for future in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[future]
            try:
                analysis = future.result()
                completed += 1
                print(f"      附件分析进度: {completed}/{len(html_files)}")
                if analysis:
                    results.append((name, analysis))
            except Exception as e:
                print(f"      分析 {name} 失败: {e}")

    if not results:
        return ""

    parts = [
        f"### {name}\n\n[原型稿分析]\n{analysis}\n[/原型稿分析]"
        for name, analysis in results
    ]
    return "\n## 需求附件\n\n" + "\n\n".join(parts) + "\n"


# =============================================================================
# 主函数
# =============================================================================


def get_story(story_id: str, workspace_id: Optional[str] = None) -> None:
    """
    从 TAPD 获取需求（Story）详情并打印

    Args:
        story_id: 需求 ID（支持短 ID 或长 ID）
        workspace_id: 工作区 ID，可选。未提供时从 .env 读取

    Exits:
        当 workspace_id 未提供且 .env 中也未配置时，程序退出并返回错误码 1
    """
    workspace_id = workspace_id or os.environ.get("TAPD_WORKSPACE_ID", "")

    if not workspace_id:
        print("Error: the following arguments are required: --workspace")
        sys.exit(1)

    # 转换短 ID 为长 ID
    long_story_id = to_long_id(story_id, workspace_id)

    response: StoryListResponse = make_request(
        "GET",
        "/stories",
        params={
            "id": long_story_id,
            "workspace_id": workspace_id,
            "fields": "id,name,description",
            "limit": 1,
        },
    )

    # 检查 data 是否为空
    if not response.get("data"):
        print(f"Error: Story not found with ID '{long_story_id}'")
        sys.exit(1)

    # 提取 story
    story = response["data"][0]["Story"]

    enriched_text = enrich_description_with_vision(story["description"], workspace_id)

    attachment_section = parse_attachments(long_story_id, workspace_id)

    print("✓ 需求解析完成")

    # 构造 agent_prompt
    agent_prompt = f"""以下是需求详情（其中图片已转换为文字描述）：

## 需求名称

{story["name"]}

## 需求内容

{enriched_text}
{attachment_section}
请根据以上需求进行分析/拆解/开发。
"""

    # 写入 prd.md
    prd_file = Path.cwd() / "stories" / long_story_id / "prd.md"
    prd_file.parent.mkdir(parents=True, exist_ok=True)
    prd_file.write_text(agent_prompt, "utf-8")

    print(agent_prompt)


# =============================================================================
# CLI 入口
# =============================================================================

if __name__ == "__main__":
    load_env()

    parser = argparse.ArgumentParser(description="获取需求详情")
    parser.add_argument("--story", "-s", required=True, help="Story ID")
    parser.add_argument("--workspace", "-w", required=False, help="Workspace ID")

    args = parser.parse_args()

    get_story(args.story, args.workspace)
