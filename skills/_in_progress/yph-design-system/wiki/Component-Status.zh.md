系统中的组件（Component）会使用状态标签（Status Label）来标识其完成状态。这通过 `status` 选项实现：

```html
<script>
  /**
   * My Heading component
   */
  export default {
    name: "Heading",
    status: "prototype",
    release: "1.0.0"
  }
</script>
```

具体示例参见 [ExampleComponent.vue](https://github.com/arielsalminen/vue-design-system/blob/master/src/ExampleComponent.vue#L18-L30)。所有可用状态如下所示：

| 标签         | 颜色         | 描述                            |
| ------------- | ------------- | -------------------------------------- |
| deprecated    | 红色           | 组件已弃用（Deprecated）                |
| prototype     | 蓝色          | 原型（Prototype），请勿投入使用！           |
| under-review  | 黄色        | 组件正在审核中  |
| ready         | 绿色         | 可以投入使用。                      |

有关在活文档（Living Documentation）中的实际展示效果，参见 [Vue Design System 示例文档](https://vueds.com/example/)
