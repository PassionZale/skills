Vue Design System 使用以下框架和 Sass Mixin（混入）来创建可预测且和谐的间距（Spacing）。

* **Inset spacing（内嵌间距）：** 适用于所有用户界面容器。
* **Inset squish spacing（压缩内嵌间距）：** 与内嵌间距类似，但压缩内嵌会减小上下间距，例如减少 50%。用于按钮、输入框、数据表格单元格、列表项等。
* **Stack spacing（堆叠间距）：** 适用于所有堆叠内容。例如面板、表单字段以及任何垂直堆叠的元素。
* **Inline spacing（行内间距）：** 适用于标签（Pills）、标记（Tags）、面包屑导航（Breadcrumbs）、并排表单字段等。即以行内方式显示的元素。

你可以通过 Sass Mixin 来使用这些间距，如下所示：

```scss
// Stack space
.heading {
  @include stack-space($space-l);
}
// Inset space
.container {
  @include inset-space($space-xl);
}
// Inline space
.pill {
  @include inline-space($space-s);
}
// You can also combine inset/inset-squish and inline/stack space
.button {
  @include inset-squish-space($space-l);
  @include inline-space($space-s);
}
```

如果你想进一步调整这些 Sass 辅助工具，它们位于 [src/styles/_spacing.scss](https://github.com/arielsalminen/vue-design-system/blob/master/src/styles/_spacing.scss)。

## 优势：

* 大多数组件已内置使用上述 Mixin 的间距。
* 开发者只需排列组件，组件会自动处理间距。
* 通过间距 Mixin 内部的高级 CSS 选择器，系统性地解决了组件级间距与内嵌间距之间的冲突。

## 参考资源：

这些理念主要来自以下文章：

* Space in Design Systems: https://medium.com/eightshapes-llc/space-in-design-systems-188bcbae0d62
* A framework for creating a predictable & harmonious spacing system for faster design-dev handoff: https://blog.prototypr.io/a-framework-for-creating-a-predictable-and-harmonious-spacing-system-8eee8aaf773c
* Padding in Lightning Design System: https://www.lightningdesignsystem.com/utilities/padding
