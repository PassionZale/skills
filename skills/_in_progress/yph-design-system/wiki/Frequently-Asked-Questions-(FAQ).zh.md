## 什么是 Vue Design System？

Vue Design System 是一个用于构建 UI 设计系统（Design System）的开源工具，基于 [Vue.js](https://vuejs.org) 开发。它为你的团队提供了一套有条理的工具、模式（Pattern）和实践方法，作为应用开发的基础。[了解更多](https://arie.ls/2018/vue-design-system/)。

## 支持哪些浏览器？

开发环境支持以下浏览器。如需调整生产环境所支持的浏览器，请编辑 [package.json 中的 browsers list](https://github.com/arielsalminen/vue-design-system/blob/master/package.json#L172-L180)。要查看当前 browsers list 选中了哪些浏览器，在项目根目录下运行 `npx browserslist --config="package.json"` 即可。

| 浏览器          | 版本   |
| --------------- | ------ |
| Google Chrome   | 最新版 |
| Microsoft Edge  | 最新版 |
| Mozilla Firefox | 最新版 |
| Opera           | 最新版 |
| Safari          | 最新版 |

## 如何快速上手？

参见 GitHub 上的[快速入门指南](https://github.com/arielsalminen/vue-design-system/wiki/getting-started)。

## 我想在已有的 Vue 项目中使用，可以吗？

完全可以，参见[快速入门指南](https://github.com/arielsalminen/vue-design-system/wiki/getting-started#using-vue-design-system-in-an-existing-project)中的相关说明。

## 为什么选择 Vue 而不是 React、Jekyll 或其他工具？

**简短回答：** 这是我在与客户合作过程中发现的一个个人偏好。

**详细回答：** 之所以选择 Vue.js 而非 React 或其他库，原因在于 Vue.js 的学习曲线非常平缓。只要你了解 HTML、CSS 以及一些 JavaScript，就可以上手使用这个工具并参与其中。当我们希望让设计师更多地参与到开发流程中，并进一步摆脱静态设计工具时，这一点尤为重要。此外，像 Jekyll 这样的静态站点生成器给予了过多的自由度，反而使得团队难以遵循特定的规范或工作流。

## Atomic Design 中的分子（Molecule）和页面（Page）层级去哪了？

与 Atomic Design 相比，本项目的设定中不包含分子/页面层级。省略这些层级是为了降低系统的复杂度，方便最终用户使用。

## 这个工具仅适用于基于 Vue.js 的应用吗？

拥有多种技术栈应用的组织同样可以受益于 Vue Design System。存储视觉设计属性的设计令牌（Design Token）具有通用性，可在任何平台上使用。Vue Design System 同时以 Vue.js 和 HTML 两种形式渲染所有组件，使你能够在任何基于 Web 的平台上使用这些组件。此外，还可以通过配置构建流程输出 Web Components，而非 Vue.js 组件。

## 为什么默认没有提供更多组件？

Vue Design System 不是前端组件库，也永远不会是。相反，它致力于为你的团队提供一套有条理的工具、模式和实践方法，作为构建基础，帮助你更快地启动实际的设计系统工作。

## 能否将 YAML 设计令牌转换为 SCSS 和 JSON 以外的格式？

当然可以。参见 [Theo 文档](https://github.com/salesforce-ux/theo)。它支持将设计令牌转换为你能想到的几乎所有格式。所使用的格式在 [package.json](https://github.com/arielsalminen/vue-design-system/blob/master/package.json#L25) 中进行配置。

## Vue Design System 可以在 Windows 上运行吗？

可以，按照[快速入门指南](https://github.com/arielsalminen/vue-design-system/wiki/getting-started)操作即可。

## 有支持不同组件状态的计划吗？

Vue Design System 在样式指南部分使用了定制版的 [Vue Styleguidist](https://github.com/vue-styleguidist/vue-styleguidist)，后者已经支持类似功能。例如，你可以在组件的 `<docs>` 区块中以 markdown 格式定义多个示例。我在文档的[元素（Element）部分](/#/Elements?id=forminput)添加了一个相关示例。更多细节请参阅 [Vue Styleguidist 文档](https://github.com/vue-styleguidist/vue-styleguidist)以及 React Styleguidist 关于 [Storybook 与 Styleguidist 区别的说明](https://react-styleguidist.js.org/docs/cookbook.html#whats-the-difference-between-styleguidist-and-storybook)。

## 如何查看可用的图标？

图标位于 `src/assets/icons` 目录中，你可以直接添加所需的任何图标。例如，可以使用来自 [Font Awesome](https://github.com/encharm/Font-Awesome-SVG-PNG/tree/master/black/svg) 的 SVG 文件。

## 如何更改默认字体？

Vue Design System 使用 Typekit 的 [Web Font Loader](https://github.com/typekit/webfontloader)，配置非常简单。要加载自定义字体文件，请参阅 [WebFontLoader 入门指南](https://github.com/typekit/webfontloader#get-started)。目前应用从 Google Fonts 加载 _Fira Sans_ 及若干不同字重。参见 `src/utils/webFontLoader.js` 中的示例。

如果你希望将字体打包到项目中，同样可以实现。我创建了一个单独的分支来演示这一方式，参见[该 commit](https://github.com/arielsalminen/vue-design-system/commit/a7b3badb618fb5e0e1c999940b8ea82e86aea190) 中的修改。

## 如何在 JavaScript 中使用设计令牌？

首先，在需要使用设计令牌的组件中导入它们：

```html
<script>
  import designTokens from "@/assets/tokens/tokens.raw.json";
</script>
```

然后，将数据传递给模板：

```html
<script>
export default {
  data() {
    return {
      tokens: designTokens.props
    };
  }
};
</script>
```

完成后，即可在 `<template>` 中使用设计令牌，示例如下：

```html
<template>
  <Thing :style="{color: tokens.color_vermilion.value}" />
</template>
```

## 如何使用在设计令牌中定义的媒体查询？

```scss
.wrapper {
  padding: $space-l;
  @media #{$media-query-l} {
    padding: $space-xl;
  }
}
```

## 如何禁止浏览器自动打开新窗口？

移除 [package.json 中这一行](https://github.com/arielsalminen/vue-design-system/blob/master/package.json#L24)的 `--open` 选项即可。

## 如何使用静态图片资源？

你可以将资源放置在 `src/assets` 目录下，也可以在该目录下创建新的子目录。由于 Vue 应用端使用 Webpack 来引入所有静态资源，你需要按以下方式定义路径，以确保其在应用和样式指南中均能正常工作：`<img src="@/assets/img/example.jpg" />`。

对于组件的 `<docs>` 区块，情况略有不同。在那里使用 `<img src="img/example.jpg" />`（不带 `@/assets/`）即可。这是因为 [Styleguidist](https://github.com/vue-styleguidist/vue-styleguidist) 对资源目录的处理方式有所不同。

## Vue Design System 可以与 Nuxt.js 配合使用吗？

可以！虽然目前尚无详尽的文档说明，但已提供了官方示例和说明，参见：[github.com/arielsalminen/nuxt-design-system](https://github.com/arielsalminen/nuxt-design-system)。

## 无法将 Vue Design System 作为 NPM 依赖正常运行？

请先查看官方示例：[github.com/arielsalminen/vue-design-system-example](https://github.com/arielsalminen/vue-design-system-example)。如果遇到 `export 'default' was not found` 错误，很可能是你试图将提供的 UMD 模块当作 ES Module 来导入。

## 我想使用 CSS Modules，是否支持？

支持，但需要在 Webpack 构建配置中添加以下内容：

```js
options: {
  // enable CSS Modules
  modules: true,
  // customize generated class names
  localIdentName: '[local]_[hash:base64:8]'
}
```

更详细的说明请参阅：[vue-loader.vuejs.org/guide/css-modules.html](https://vue-loader.vuejs.org/guide/css-modules.html)

## 能否在静态网站上使用系统中的组件？

可以。参见 GitHub 上的官方示例：[github.com/arielsalminen/vue-design-system-example-website](https://github.com/arielsalminen/vue-design-system-example-website)
