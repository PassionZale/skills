# 创建任务

基于需求的拆分结果创建任务。

## 步骤

### Step 1 - 数据转换

将拆分结果 `${PWD}/tasks/<story_id>/task.md` 写入 `${PWD}/tasks/<story_id>/task.json`:

```json
[
  {
    "domain": "domain, 例如: yos-web, 不存在则为 null",
    "dimension": "任务维度, 例如: C1",
    "name": "任务名称",
    "description": "任务描述",
    "effort": "任务工时 (number)"
  }
]
```

### Step 2 - 创建任务

若用户确认任务拆分结果无误，执行 `python3 ${BASE_DIR}/scripts/create_tasks.py` 批量创建。

参数:

- 需求ID: story_id (number)
- 文件路径: file (绝对路径)
- 工作空间ID: workspace_id (number)（可选）

示例:

```bash
python3 ${BASE_DIR}/scripts/create_tasks.py --s <story_id> --f tasks/<story_id>/task.json

python3 ${BASE_DIR}/scripts/create_tasks.py --s <story_id> --f tasks/<story_id>/task.json --w <workspace_id>
```

脚本会按顺序逐条调用 TAPD API，每条任务创建成功后打印结果。

**在用户明确确认前不得自动执行此步骤。**
