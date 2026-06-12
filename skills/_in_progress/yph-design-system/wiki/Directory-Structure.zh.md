以下是设计系统（Design System）的基本结构。系统的组成部分被划分为 `tokens`、`elements`、`patterns` 和 `templates`，详见[术语表](https://github.com/arielsalminen/vue-design-system/wiki/Terminology)。

此外还有 `styles` 目录，其中包含通用的 `functions`、`mixins` 和 `variables`，供按需使用。例如，当前提供了一组函数，可以基于 `tokens` 中定义的颜色生成色阶（tints）和暗色变体（shades）。

`assets` 目录用于存放图标、字体等静态资源文件。

`Router` 将模板（Template）映射到路由，并告知 vue-router 何时以及在何处渲染它们。

`docs` 目录包含显示在活文档（Living Documentation）中的所有自定义内容。

`config` 目录包含活文档、开发环境及构建流程的配置。

最后，`test` 目录包含 Vue 设计系统的单元测试。

```
├─ src
│   ├─ tokens
│   ├─ elements
│   ├─ patterns
│   ├─ templates
│   ├─ styles
│   ├─ router
│   ├─ utils
│   ├─ assets
│   │   └─ icons
│   ├─ App.vue
│   ├─ ExampleComponent.vue
│   ├─ main.js
│   └─ system.js
├─ docs
│   ├─ utils
│   └─ components
│       ├─ tokens
│       └─ status
├─ config
├─ test
│   └─ unit
├─ build
└─ dist
```
