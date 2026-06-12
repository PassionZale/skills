## 概述

有以下几种方式可以将 Vue Design System（Vue 设计系统）集成到你的应用中：

* 推荐方式是将 Vue Design System 与应用分离，通过 NPM（作为私有依赖）来使用该系统库。
* 如果你 *只有* 一个应用，也可以将所有内容放在同一项目中，因为文档和应用逻辑是分离的。但这不是推荐方式，因为其可扩展性较差。
* 对于系统原型开发和入门，我仍然推荐上述方法，因为这是最快的起步方式，且几乎不需要任何配置。当系统足够成熟后，你可以转向将其作为 NPM 依赖来使用。
* 拥有非 Vue.js 应用的组织同样可以从 Vue Design System 中受益。存储视觉设计属性的 Design Token（设计令牌）是通用的，可以在任何平台上使用。

## 快速开始

通过克隆仓库并安装依赖来开始：

```bash
git clone https://github.com/arielsalminen/vue-design-system.git
cd vue-design-system
npm install
```

请确保你已安装最新版本的 [Node.js](https://nodejs.org/en/) _（至少 8.2.1）_。

安装依赖后，运行以下命令即可启动并运行 Vue 应用，访问地址为 [http://localhost:8080](http://localhost:8080)。同时也会启动并运行 Living Documentation（活文档），访问地址为 [http://localhost:6060](http://localhost:6060)。以下说明在 macOS 和 Windows 上均适用。

```bash
npm start
```

设计系统启动并运行后，以下资源可以帮助你继续前进：

1. [示例组件](https://github.com/arielsalminen/vue-design-system/blob/master/src/ExampleComponent.vue)
2. [术语表](https://github.com/arielsalminen/vue-design-system/wiki/terminology)
3. [目录结构](https://github.com/arielsalminen/vue-design-system/wiki/directory-structure)
4. [命名规范](https://github.com/arielsalminen/vue-design-system/wiki/naming-of-Things)
5. [使用系统](https://github.com/arielsalminen/vue-design-system/wiki/working-with-the-system)
6. [编辑活文档](https://github.com/arielsalminen/vue-design-system/wiki/editing-living-documentation)
7. [间距](https://github.com/arielsalminen/vue-design-system/wiki/spacing)
8. [组件状态](https://github.com/arielsalminen/vue-design-system/wiki/Component-Status)

## 在已有项目中使用 Vue Design System

推荐方式是将 Vue Design System 与现有应用分离，将设计系统库作为私有 NPM 依赖来使用。这基本上意味着你的系统的基础 Design Token（设计令牌）、Element（元素）和 Pattern（模式）存在于系统项目中，仅在使用时导入到现有应用中。

这样做的好处是，所有应用都将拥有一个集中的唯一事实来源（Single Source of Truth），更易于扩展和维护。请参阅下方关于如何通过 NPM 使用 Vue Design System 的说明。

## 将设计系统作为 NPM 模块使用

要实现这一点，你需要完成以下几步。虽然 `package.json` 已经为此类用途做好了准备，但在运行构建脚本之前，你需要重命名项目。在 `package.json` 中找到以下行来为你的设计系统命名：

```json
"name": "vue-design-system",
```

重命名项目后，你应该可以通过运行以下命令来为生产环境构建 Design System（设计系统），使其能够作为 NPM 模块发布和使用：

```bash
npm run build:system
```

此命令将首先以 JSON 和 SCSS 格式重新生成你的 Design Token（设计令牌），然后构建设计系统库。完成后，你应该能看到已创建的资源列表及其文件大小。使用默认配置时，这将在 `dist/system` 目录下生成 `system.js`、`system.css` 和 `system.utils.scss`。

完成后，你可以通过将系统安装到另一个 Vue 项目中来在本地测试一切是否正常（你需要更改路径以匹配你自己的文件系统）：

```bash
npm install --save file:/Users/arielle/code/vue-design-system
```

设计系统模块安装成功后，你可以在 `main.js` 文件中像这样导入系统 _（请记住将 "vue-design-system" 替换为你在 package.json 中使用的名称）：_

```js
import DesignSystem from 'vue-design-system'
import 'vue-design-system/dist/system/system.css'

Vue.use(DesignSystem)
```

所有组件、Pattern（模式）和 Template（模板）现在应该已被自动导入，并且可以像在 Design System（设计系统）内部一样使用。

要查看实现以上所有步骤的简化演示项目，请参考[我创建的仓库](https://github.com/arielsalminen/vue-design-system-example)。

对于更高级的需求，你可以通过编辑 [build-system.js](https://github.com/arielsalminen/vue-design-system/blob/master/build/build-system.js)、[webpack.system.conf.js](https://github.com/arielsalminen/vue-design-system/blob/master/build/webpack.system.conf.js) 以及 [config/index.js](https://github.com/arielsalminen/vue-design-system/blob/master/config/index.js) 中的系统配置来自定义 Webpack 构建库的方式。

## 构建设计系统 Playground 用于生产环境

为生产环境构建 Vue.js 应用（Playground）并进行代码压缩：

```bash
npm run build:app
```

为生产环境构建 Vue.js 应用（Playground）并查看 Bundle Analyzer（包分析器）报告：

```bash
npm run build:app --report
```

## 构建设计系统文档用于生产环境

为生产环境构建文档：

```bash
npm run build:docs
```

## 运行测试

使用 ESLint 进行代码检查：

```bash
npm run lint
```

使用 Jest 运行单元测试：

```bash
npm run test
```

## 所有可用的构建命令

* `npm run build:system` 为 NPM 构建设计系统
* `npm run build:system --report` 为 NPM 构建设计系统并生成 Bundle Analyzer（包分析器）报告
* `npm run build:docs` 构建设计系统文档
* `npm run build:app` 构建 Vue 应用
* `npm run build:app --report` 构建 Vue 应用并生成 Bundle Analyzer（包分析器）报告

## 关于 Webpack

有关 Webpack 工作原理的更多详细信息，请查阅 [Webpack 指南](http://vuejs-templates.github.io/webpack/)和 [vue-loader 文档](http://vuejs.github.io/vue-loader)。
