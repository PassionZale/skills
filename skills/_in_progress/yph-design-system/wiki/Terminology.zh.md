设计系统（Design System）可以帮助组织内所有人建立一套通用词汇表。正因如此，我花了大量时间为 [Vue Design System](https://vueds.com/) 设计合理的结构和命名方式。为了便于理解，让我们逐一详细了解每个层级及其含义：

![Vue Design System 的结构](https://arie.ls/img/blog/2018/vue-design-system/vueds.svg)

* **原则（Principles）** 是整个系统的基础。它们构成了优秀产品的基石，并帮助团队进行决策。当你在处理系统中繁多的各个部分时，原则可以指导你和你的团队，帮助你们做出更明智的决策。
* **设计令牌（Design Tokens）** 正如 [Salesforce](https://www.lightningdesignsystem.com/design-tokens/) 所描述的，是系统的原子。在 Vue Design System 中，设计令牌被用来替代硬编码值，以确保跨平台的一致性。
* **元素（Elements）** 利用了令牌层级上所做的决策。元素的一个简单示例是按钮、链接或输入框，即任何无法进一步拆分的事物。我使用"元素"这一名称，因为在 Vue 和 React 的世界里，如今一切都可以被称为"组件"（Component）。如果再用这个术语来称呼其他东西，就会造成混淆。
* **模式（Patterns）** 是位于复杂度光谱较高端的 UI 模式。例如日期选择器、数据表格或可视化图表。模式同时利用了元素和令牌。如果你不确定某个东西应该被称为元素还是模式，可以问自己这个问题：_"它能被拆解成更小的部分吗？"_ 如果答案是肯定的，那么在 Vue Design System 中它很可能应该是一个模式。
* **模板（Templates）** 用于记录某个区块的布局和结构。我不称其为"页面"，因为在语义上那是不准确的。虽然它们_可以是_页面，但这并非其唯一功能。模板由上述三者组成：*令牌*、*元素*和*模式*。

## 系统层级，以树形结构展示：

```bash
Template
 ├─ Pattern
 │   ├─ Element
 │   │   ├─ Token
 │   │   └─ Token
 │   └─ Element
 │       └─ Token
 └─ Pattern
     └─ Element
         ├─ Token
         └─ Token
```
