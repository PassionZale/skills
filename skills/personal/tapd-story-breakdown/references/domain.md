# Domain 映射关系

每个 domain key 对应一个 repomix 打包的 agent skill，以及该 domain 所负责的业务模块。

| Domain Key         | 业务模块                         | 上手指南                                                 |
| ------------------ | -------------------------------- | -------------------------------------------------------- |
| `domain1`          | 模块1、模块2     | `references/domains/domain1-reference/SKILL.md`          |

## 使用示例

- 当用户指定 `--domain domain1` 时，只处理需求文档中属于「模块1 / 模块2」的部分。
- 当用户未指定 `--domain` 时，根据需求文档内容判断涉及哪些 domain。
- 多个 domain 用逗号分隔：`--domain domain1,domain2`，此时合并所有相关需求并分 domain 输出任务。
- 如果需求文档中提到的业务模块无法匹配任何 domain，则跳过匹配。

## Domain 文件说明

### `SKILL.md`

项目 agent skill 知识库，包含：

- 项目架构概览
- 技术栈说明
- 目录结构
- 核心业务模块
- 开发约定
- 常用代码模式
