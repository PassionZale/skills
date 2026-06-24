#!/usr/bin/env python3

"""
同步项目代码库到 TAPD Story Breakdown domains 参考目录

Usage:
    python3 sync_domains.py --p /Users/zhanglei/Documents/project1,/Users/zhanglei/Documents/project2
    python3 sync_domains.py --paths /absolute/path/project1,/absolute/path/project2
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="同步项目代码库到 domains 参考目录"
    )
    parser.add_argument(
        "--paths",
        "-p",
        required=True,
        help="项目路径列表，逗号分隔（支持绝对路径和相对路径）"
    )
    args = parser.parse_args()

    # 计算 BASE_DIR
    BASE_DIR = Path(__file__).parent.parent

    # 解析路径列表
    raw_paths = args.paths.split(",")
    paths = [Path(p.strip()).expanduser().resolve() for p in raw_paths]

    # 配置文件路径
    config_path = BASE_DIR / "repomix.config.json"

    print(f"准备处理 {len(paths)} 个项目...")

    success_count = 0

    for idx, path in enumerate(paths, 1):
        folder_name = path.resolve().name
        output_dir = BASE_DIR / "references" / "domains" / f"{folder_name}-reference"

        print(f"\n[{idx}/{len(paths)}] 处理 {folder_name}")
        print(f"  源路径: {path}")
        print(f"  输出到: {output_dir}")

        try:
            cmd = [
                "npx",
                "repomix",
                str(path),
                "--skill-generate",
                f"{folder_name}-reference",
                "--skill-output",
                str(output_dir),
                "--config",
                str(config_path),
                "--force",
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"  ✓ {folder_name} 同步完成")
            success_count += 1
        except subprocess.CalledProcessError as e:
            print(f"  ✗ {folder_name} 同步失败:")
            if e.stderr:
                stderr_text = e.stderr.decode("utf-8", errors="ignore")
                print(f"    {stderr_text.strip()}")
            else:
                print(f"    {str(e)}")

    # 输出统计
    print(f"\n{'='*60}")
    print(f"同步完成: {success_count}/{len(paths)} 成功")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
