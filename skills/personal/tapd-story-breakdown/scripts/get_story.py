#!/usr/bin/env python3

"""
从 TAPD 获取需求（Story）详情脚本

功能：
- 支持短 ID 或长 ID 查询
- 在 {PWD}/stories/<short_id>/ 下落盘需求物料（manifest.json + intake/）
- 下载富文本内嵌图片到本地，并发调用视觉模型生成文字说明
- 下载全部附件到 intake/prototype/，HTML 原型交文本模型分析
- 输出整理后的 Markdown 供 LLM 理解
"""

import argparse
import json
import os
import shutil
import sys
import concurrent.futures
from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs
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
    to_short_id,
    analyze_image_with_vision,
    download_attachments,
    download_image,
    analyze_html_with_llm,
)
from typings import StoryListResponse, ImageResponse


# =============================================================================
# 图片处理函数
# =============================================================================


_IMAGE_EXT_CONTENT_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/svg+xml": ".svg",
}


def _image_ext(url: str, content_type: str = "") -> str:
    """
    根据下载 URL 后缀或响应 Content-Type 推断图片扩展名

    Args:
        url: 图片下载 URL
        content_type: 下载响应的 Content-Type（可选）

    Returns:
        以 . 开头的扩展名，无法识别时默认 .png
    """
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}:
        return ".jpg" if suffix == ".jpeg" else suffix

    ct = content_type.split(";")[0].strip().lower()
    return _IMAGE_EXT_CONTENT_TYPES.get(ct, ".png")


def get_tapd_image(src: str, workspace_id: str) -> tuple[str, str]:
    """
    获取图片下载 URL（不含视觉模型调用）

    支持两种 TAPD 内部图片路径：
      1. 裸相对路径：/tfl/captures/...
      2. 完整 URL 的 query string：https://file.tapd.cn/compress/...?src=/tfl/captures/...

    内部图调用 /files/get_image 换取原图下载 URL；
    非内部图，或换链失败时，回退到原 src 保证图片仍可用。

    Args:
        src: 图片 src 路径（裸 /tfl/ 路径、含 /tfl/ query 的完整 URL，或其他完整 URL）
        workspace_id: TAPD 工作区 ID

    Returns:
        (original_src, download_url) 元组
    """
    image_path = _extract_tfl_path(src)

    # 非 TAPD 内部图，直接用原 src
    if not image_path:
        return (src, src)

    try:
        response: ImageResponse = make_request(
            "GET",
            "/files/get_image",
            params={
                "workspace_id": workspace_id,
                "image_path": image_path,
            },
        )
        download_url = response["data"]["Attachment"]["download_url"]
        return (src, download_url)
    except Exception:
        # 换链失败（API 异常或字段缺失）时回退原 src，避免中断整篇解析
        return (src, src)


def _extract_tfl_path(src: str) -> str:
    """
    从 src 中提取 /tfl/ 图片路径

    支持两种形式：
      - 裸 /tfl/ 相对路径：直接返回
      - 完整 URL：从 query string 的 src 参数中提取

    提取不到返回空串。
    """
    # 形式一：裸 /tfl/ 相对路径
    if src.startswith("/tfl/"):
        return src

    # 形式二：完整 URL，从 query string 的 src 参数提取
    # parse_qs 会自动 URL 解码，%2Ftfl%2F 也能识别
    for value in parse_qs(urlparse(src).query).get("src", []):
        if value.startswith("/tfl/"):
            return value

    return ""


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


def enrich_description_with_vision(html: str, workspace_id: str, images_dir: Path) -> str:
    """
    下载富文本内嵌图片到本地，并调用视觉模型生成文字说明

    图片按出现顺序编号保存为 images/img-NN.<ext>（同一图片只下载一次），
    替换为本地相对引用，视觉分析结果以引用块形式紧跟其后。

    Args:
        html: 原始 description HTML
        workspace_id: TAPD 工作区 ID
        images_dir: 图片保存目录

    Returns:
        整理后的 Markdown description（图片引用指向本地 images/）
    """
    if not html:
        return ""

    # 1. description (html) 输入
    print(f"[1/5] 接收需求描述: ({len(html)} 字符)")

    soup = BeautifulSoup(html, "html.parser")

    # 2. 提取所有 img src 并下载到本地
    images_dir.mkdir(parents=True, exist_ok=True)

    img_info_list: list[tuple] = []  # [(img_tag, download_url, local_ref, alt), ...]
    downloaded: dict[str, str] = {}  # {download_url: 本地相对引用，空串表示已尝试但失败}
    image_payloads: dict[str, tuple[bytes, str]] = {}  # {download_url: (图片字节, Content-Type)}
    seq = 0

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or src.startswith("data:"):
            continue
        original_src, download_url = get_tapd_image(src, workspace_id)

        if download_url not in downloaded:
            content = download_image(download_url)
            if content is None:
                downloaded[download_url] = ""
            else:
                seq += 1
                data, content_type = content
                filename = f"img-{seq:02d}{_image_ext(download_url, content_type)}"
                (images_dir / filename).write_bytes(data)
                downloaded[download_url] = f"images/{filename}"
                image_payloads[download_url] = (data, content_type)

        local_ref = downloaded[download_url]
        alt = f"图片 {seq}" if local_ref else ""
        img_info_list.append((img, download_url, local_ref, alt))

    if not img_info_list:
        # 无图片，直接转 Markdown
        print("[2/5] 未检测到图片，跳过视觉分析")
        return md(str(soup), escape_asterisks=False, escape_underscores=False)

    saved_count = sum(1 for _, _, ref, _ in img_info_list if ref)
    print(f"[2/5] 检测到 {len(img_info_list)} 张图片，{saved_count} 张已下载到本地")

    # 3. 并发调用视觉模型分析每张图
    vision_results: dict[str, str] = {}  # {download_url: analysis_text}

    unique_urls = list(dict.fromkeys(url for _, url, _, _ in img_info_list if url in image_payloads))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # 构建 {url: context} 映射（同 URL 多处出现时取第一处的上下文）
        url_to_context: dict[str, str] = {}
        for img_tag, download_url, _, _ in img_info_list:
            url_to_context.setdefault(download_url, get_surrounding_text(img_tag))

        print(f"[3/5] 并发调用视觉模型分析 {len(unique_urls)} 张图片...")

        # 提交任务时传入图片字节（base64 data URI 传参，Kimi 不接受远程 URL）
        future_to_url = {
            executor.submit(
                analyze_image_with_vision,
                *image_payloads[url],
                url_to_context.get(url, ""),
            ): url
            for url in unique_urls
        }
        completed = 0
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                completed += 1
                print(f"      进度: {completed}/{len(unique_urls)}")
                if result:
                    vision_results[url] = result
            except Exception:
                pass

    # 4. 将图片替换为本地引用 + 分析说明引用块
    #    表格内的图片会被 markdownify 平铺成纯文本丢失引用，统一提升到所属表格之后
    print("[4/5] 将图片引用与说明替换回需求描述")
    moved_anchors: dict[int, object] = {}  # {table 节点 id: 该表格后最后插入的节点}

    for img_tag, download_url, local_ref, alt in img_info_list:
        note = soup.new_tag("blockquote")
        p = soup.new_tag("p")

        img_new = None
        if local_ref:
            analysis = vision_results.get(download_url, "")
            p.string = f"[图片内容说明]\n{analysis or '（视觉分析失败，请人工查看图片）'}\n[/图片内容说明]"
            note.append(p)
            img_new = soup.new_tag("img")
            img_new["src"] = local_ref
            img_new["alt"] = alt
        else:
            p.string = "[图片内容说明]（图片下载失败，原始地址见 prd.raw.html）[/图片内容说明]"
            note.append(p)

        table = img_tag.find_parent("table")
        if table is None:
            # 常规位置：原位替换
            if img_new is not None:
                img_tag.replace_with(img_new)
                img_new.insert_after(note)
            else:
                img_tag.replace_with(note)
        else:
            # 表格内：提升到表格之后，按出现顺序排列
            cursor = moved_anchors.get(id(table), table)
            if img_new is not None:
                wrapper = soup.new_tag("p")
                wrapper.append(img_new)
                cursor.insert_after(wrapper)
                wrapper.insert_after(note)
                cursor = note
            else:
                cursor.insert_after(note)
                cursor = note
            moved_anchors[id(table)] = cursor
            img_tag.decompose()

    # 5. html 转 Markdown
    print("[5/5] 需求描述解析完成")
    return md(str(soup), escape_asterisks=False, escape_underscores=False)


# =============================================================================
# 附件处理函数
# =============================================================================


def parse_attachments(story_id: str, workspace_id: str, attach_dir: Path) -> str:
    """
    下载并分析需求附件，返回附件分析文本

    Args:
        story_id: 需求长 ID
        workspace_id: 工作区 ID
        attach_dir: 附件保存目录（stories/<short_id>/intake/prototype/）

    Returns:
        附件分析文本，无附件时返回空字符串
    """
    print("[1/2] 下载原型附件...")
    html_files = download_attachments(story_id, workspace_id, attach_dir)

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


def write_manifest(
    story_dir: Path,
    long_id: str,
    short_id: str,
    title: str,
    workspace_id: str,
) -> None:
    """
    写入 manifest.json（覆盖刷新字段，但保留 agent 已改写的 slug）

    slug 初始占位为 tapd-<short_id>，由调用方 agent 在拉取后阅读需求内容改写为
    tapd-<short_id>-<语义短语>，用作 git feature 分支名。重拉时若已有 slug 与
    占位值不同，则原样保留。
    """
    manifest_file = story_dir / "manifest.json"

    existing: dict = {}
    if manifest_file.exists():
        try:
            existing = json.loads(manifest_file.read_text("utf-8"))
        except (OSError, ValueError):
            existing = {}

    slug = f"tapd-{short_id}"
    old_slug = str(existing.get("slug") or "")
    if old_slug and old_slug != f"tapd-{existing.get('short_id', short_id)}":
        slug = old_slug

    manifest = {
        "id": long_id,
        "short_id": short_id,
        "title": title,
        "slug": slug,
        "workspace_id": workspace_id,
        "url": f"https://www.tapd.cn/{workspace_id}/prong/stories/view/{long_id}",
        "updated_at": date.today().isoformat(),
    }
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8")


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
    short_id = to_short_id(long_story_id)

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

    # 准备目录结构：images/、prototype/ 覆盖式重建，ui/、docs/ 仅预创建、绝不触碰内容
    story_dir = Path.cwd() / "stories" / short_id
    intake_dir = story_dir / "intake"
    images_dir = intake_dir / "images"
    prototype_dir = intake_dir / "prototype"

    for product_dir in (images_dir, prototype_dir):
        if product_dir.exists():
            shutil.rmtree(product_dir)
        product_dir.mkdir(parents=True, exist_ok=True)

    for manual_dir in (intake_dir / "ui", story_dir / "docs"):
        manual_dir.mkdir(parents=True, exist_ok=True)
        (manual_dir / ".gitkeep").touch()

    write_manifest(story_dir, long_story_id, short_id, story["name"], workspace_id)

    # 保存 API 原始富文本快照
    (intake_dir / "prd.raw.html").write_text(story["description"] or "", "utf-8")

    enriched_text = enrich_description_with_vision(story["description"], workspace_id, images_dir)

    attachment_section = parse_attachments(long_story_id, workspace_id, prototype_dir)

    print("✓ 需求解析完成")

    # 构造 agent_prompt
    agent_prompt = f"""以下是需求详情（图片以本地相对路径引用到 images/，并附文字说明）：

## 需求名称

{story["name"]}

## 需求内容

{enriched_text}
{attachment_section}
请根据以上需求进行分析/拆解/开发。
"""

    # 写入 prd.md
    prd_file = intake_dir / "prd.md"
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
