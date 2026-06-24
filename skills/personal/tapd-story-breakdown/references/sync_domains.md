# 同步领域

将给定的项目代码库同步到 domains 中.

## 使用方式

执行 `python3 ${BASE_DIR}/scripts/sync_domains.py` 同步给定项目代码库.

参数:

- 代码库路径: paths

示例:

```bash
python3 ${BASE_DIR}/scripts/sync_domains.py --p /Users/admin/Documents/project1,/Users/admin/Documents/project2

python3 ${BASE_DIR}/scripts/sync_domains.py --paths /absolute/path/project1,/absolute/path/project2
```
