## `Tokens`

设计令牌（Design Token）是系统的原子，正如 [Salesforce](https://www.lightningdesignsystem.com/design-tokens/) 所描述的那样。在 Vue Design System 中，设计令牌被用来替代硬编码值，以确保跨平台的一致性。


### 创建新 `Token`

创建新设计令牌非常简单，只需导航到 `/src/tokens/` 并编辑任意 YAML 文件即可。强烈建议先查看 `spacing.yml` 或 `color.yml` 中已有的示例令牌。

如果需要在现有分类之外添加新类别，可以在同一目录下创建新的 YAML 文件。完成后，在 `/src/tokens/tokens.yml` 中导入新的 partial：

```yml
#
# GLOBAL: DESIGN TOKENS
#

imports:
  - color.yml
  - font-size.yml
  - font-family.yml
  - opacity.yml
  - size.yml
  - timing.yml
  - z-index.yml
  - media-query.yml
  - box-shadow.yml
  - border-radius.yml
  - spacing.yml
  - line-height.yml
global:
  type: global
  category: all
```

`Token` partial 文件本身大致如下所示，具体取决于系统的复杂度：

```yml
#
# SPACING TOKENS
# Use these tokens to set padding, margin and position coordinates.
#

props:
  space_xxl:
    value: "128px"
  space_xl:
    value: "64px"
  space_l:
    value: "48px"
  space_m:
    value: "24px"
  space_s:
    value: "16px"
  space_xs:
    value: "8px"
global:
  type: number
  category: space

```


### 在 SCSS 中使用 `Token`

由于令牌是全局导入的，你可以在任何 `Element`、`Pattern` 或 `Template` 中直接使用，无需额外配置。使用令牌非常简单：

```html
<style lang="scss" scoped>
  a {
    font-family: $font-primary;
  }
</style>
```

Vue Design System 使用 [Theo](https://github.com/salesforce-ux/theo) 将设计令牌从 YAML 转换并格式化为 JSON 和 SCSS 两种格式。要了解更多关于使用和格式化 `Token` 的信息，请参阅 [Theo 的文档](https://github.com/salesforce-ux/theo)。

### 在 JS 中使用 `Token`

* **[参见 FAQ](https://github.com/arielsalminen/vue-design-system/wiki/Frequently-Asked-Questions-(FAQ)#i-want-to-use-design-tokens-in-javascript-as-well-is-that-possible)**


## `Elements`

元素（Element）是 UI 中最小的基本结构，无法再进一步拆分。按钮、链接和输入框就是典型的例子。元素使用 `Token`。

### 创建新 `Element`

要创建新元素，首先导航到 `/src/elements/` 并创建一个新的 `.vue` 文件。元素名称没有前缀，但建议确保它们与现有和未来的 HTML 元素兼容*（了解更多信息，请参见 [命名规范](#naming-of-things)）*。

### 为简单起见，假设你要创建一个按钮：

首先，将文件命名为例如 `Button.vue`。

创建文件后，接下来需要熟悉 [Vue 模板及其工作方式](https://vuejs.org/v2/guide/single-file-components.html)。基本结构如下：

```html
<template>
  <!-- Your element's HTML -->
</template>

<script>
  // Your element's JS
</script>

<style>
  /* Your element's CSS */
</style>
```

*看起来很简单，对吧？*

现在，添加一些模板标记。这是一个按钮，所以我们添加一个基本的 HTML `<button>` 和一个 `<slot />`。*Slot*（插槽）用于允许父级 `Pattern` 向子级 `Element` 传递 DOM 元素。

```vue
<template>
  <button class="button">
    <slot />
  </button>
</template>
```

进一步地，我们还可以为 `<slot />` 添加默认内容，当没有内容传入时会显示该默认值：

```vue
<template>
  <button class="button">
    <slot>I'm a Button!</slot>
  </button>
</template>

<script>
  export default {
    name: "Button",
    status: "prototype",
    release: "1.0.0"
  }
</script>

<style lang="scss" scoped>
  .button {
    font-family: $font-primary;
    background: $color-rich-black;
    color: $color-white;
  }
</style>
```

在上面的示例中，我还添加了一些使用设计系统 `Token` 的基本样式属性。`<style>` 中的 *scoped* 属性意味着此 SCSS 仅应用于当前 `Element`，这与 Shadow DOM 中的样式封装类似。

关于向 `Element` 和 `Pattern` 传递 `props` 的更多示例，请参见下方。

#### 带自定义 `props` 的 `Element` 示例：

```vue
<template>
  <a :href="href">
    <slot />
  </a>
</template>

<script>
  export default {
    name: "Link",
    status: "prototype",
    release: "1.0.0",
    props: ["href"],
  }
</script>
```

#### 使用上述 `Element` 和 `props` 的 `Template` 示例：

```vue
<template>
  <Link href="https://arie.ls/">
    This is a label!
  </Link>
</template>

<script>
  export default {
    name: "MyTemplate",
    status: "prototype",
    release: "1.0.0"
  }
</script>
```

如你所见，我们还在 `Element` 内部添加了一些文本内容来覆盖默认的 `<slot />` 内容。如果需要，也可以直接使用元素并显示默认的 *slot* 内容：

```vue
<template>
  <Link />
</template>
```


## `Patterns`

模式（Pattern）是复杂度较高的 UI 模式。模式可以由 `Element` 和 `Token` 共同组成。

`Pattern` 和 `Element` 遵循完全相同的规则。从 Vue.js 的角度来看，它们都是 `Vue Components`（Vue 组件），但为了便于不同团队、学科和利益相关者之间的沟通，系统需要一套统一的术语和层级体系。

要更好地理解本项目中使用的层级和术语，请参阅 [系统层级结构部分](https://github.com/arielsalminen/vue-design-system/wiki/terminology#hierarchy-visualized)。


## `Templates`

模板（Template）用于记录某个区域或整个界面的布局与结构。模板可以由 `Pattern`、`Element` 和 `Token` 共同组成。
