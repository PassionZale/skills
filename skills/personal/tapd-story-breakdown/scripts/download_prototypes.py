"""下载 PRD 中的原型页面并更新引用。

URL 筛选（原型域名白名单）在 SKILL.md 规则层，由调用方显式传入；
本脚本只负责执行：下载静态 HTML → 按语义名保存到 prototype/ → 替换 prd.md 引用。
"""

import argparse
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
import urllib3

# 原型站点可能使用自签名证书，跳过校验
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def download_prototype(url: str, save_dir: Path) -> tuple[Path | None, str]:
    """下载单个原型页面，返回 (保存路径, 消息)。失败时路径为 None。"""
    file_name = Path(unquote(urlparse(url).path)).name
    if not file_name:
        return None, "无法从 URL 推导文件名"
    save_path = save_dir / file_name
    try:
        resp = requests.get(url, verify=False, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        return None, f"下载失败: {e}"
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(resp.content)
    return save_path, f"OK ({len(resp.content)} bytes)"


def main() -> None:
    parser = argparse.ArgumentParser(description="下载原型页面 HTML 并替换 prd.md 中的远程引用")
    parser.add_argument("--f", required=True, help="prd.md 文件路径")
    parser.add_argument("urls", nargs="+", help="原型页面 URL 列表（由调用方按白名单筛选）")
    args = parser.parse_args()

    prd_path = Path(args.f).resolve()
    if not prd_path.exists():
        raise SystemExit(f"文件不存在: {prd_path}")
    content = prd_path.read_text(encoding="utf-8")
    save_dir = prd_path.parent / "prototype"

    print(f"待下载 {len(args.urls)} 个原型页面")
    for url in args.urls:
        save_path, msg = download_prototype(url, save_dir)
        if save_path is None:
            print(f"  [失败] {url}\n         {msg}，保留原 URL")
            continue
        ref = f"prototype/{save_path.name}"
        # 优先整体替换 markdown <URL> 包裹形式，避免残留尖括号
        content = content.replace(f"<{url}>", ref).replace(url, ref)
        print(f"  [下载] {save_path.name} {msg}\n         引用已替换为 {ref}")

    prd_path.write_text(content, encoding="utf-8")
    print(f"完成，PRD 引用已更新: {prd_path}")


if __name__ == "__main__":
    main()
