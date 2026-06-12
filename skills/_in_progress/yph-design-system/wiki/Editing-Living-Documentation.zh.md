系统组件的文档基于源代码中的注释以及 `/docs/` 目录下的 readme 文件生成。每个 `元素`、`模式` 和 `模板` 还可以包含一个名为 `<docs/>` 的自定义块，用于提供标记示例。如下所示：

````vue
<docs>
  ```jsx
  <wrapper>I'm an example that will be shown in docs.</wrapper>
  ```
</docs>
````

此外，你可以在 `<script/>` 中包含 JSDoc 风格的注释块，这些注释将会显示在文档中。示例如下：

````vue
<script>
  /**
   * A wrapper element is used to wrap elements and patterns.
   */
  export default {
    name: "Wrapper",
    status: "prototype",
    version: "1.0.0",
    props: {
      /**
       * The html element name used for the wrapper.
       */
      type: {
        type: String,
        default: "div"
      }
    }
  }
</script>
````

最终，添加了完整文档的 wrapper `元素` 如下所示：

````vue
<template>
  <component :is="type" class="wrapper">
    <slot/>
  </component>
</template>

<script>
  /**
   * A wrapper element is used to wrap elements and patterns.
   */
  export default {
    name: "Wrapper",
    status: "prototype",
    version: "1.0.0",
    props: {
      /**
       * The html element name used for the wrapper.
       */
      type: {
        type: String,
        default: "div"
      }
    }
  }
</script>

<style lang="scss" scoped>
  .wrapper {
    @include reset;
    @include inset-space($space-large);
    width: 100%;
  }
</style>

<docs>
  ```jsx
  <wrapper>I'm an example that will be shown in docs.</wrapper>
  ```
</docs>
````

如需了解更多关于文档格式及其用法，请参阅 GitHub 上的 [Vue Styleguidist 官方文档](https://github.com/vue-styleguidist/vue-styleguidist/tree/master/docs)。
