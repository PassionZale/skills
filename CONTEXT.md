# Skills

PassionZale 个人助理的技能集合。本词汇表沉淀技能设计中的领域语言。

## Language

**Environment (env)**:
配置驱动的部署环境标识。环境的集合完全由配置决定，不固定；每个环境映射到一个 Target Branch 和一个 Job Name。
_Avoid_: stage, tier

**Source Branch**:
一次 MR 的来源分支。默认取当前检出的分支。
_Avoid_: from-branch

**Target Branch**:
一次 MR 的目标分支。默认由 Environment 映射得出；显式指定的分支优先于环境映射。
_Avoid_: base branch

**Job Name**:
Environment 对应的 Jenkins 构建任务名。
_Avoid_: build task
