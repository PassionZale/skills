我们使用**名称**来沟通 `Tokens`（令牌）、`Elements`（元素）、`Patterns`（模式）和 `Templates`（模板）。因此，它们必须简短、有意义且可发音。每个名称必须满足：

* **动词优先于名词（Verb Rather Than Noun）：** 要理解其用途，应关注它做什么，而不是你认为它是什么。这有助于我们拓宽潜在的使用场景，同时更准确地定义其用途。
* **有意义：** 不过于具体，也不过于抽象。
* **简短：** 最多 2 到 3 个单词。
* **可发音：** 我们需要能够口头讨论它们。
* **首字母大写：** 我们建议组件名称以大写字母开头，以免与 HTML 标签混淆。
* **符合自定义元素规范（Custom Element Spec）：** 不要使用保留名称。保留名称包括：

```bash
 * annotation-xml      * color-profile
 * font-face           * font-face-src
 * font-face-uri       * font-face-format
 * font-face-name      * missing-glyph
```

## 名称前缀

关于前缀的使用有几条规则，遵循这些规则可以保持系统的一致性：

* **Tokens（令牌）：** 令牌名称始终以类别名称和连字符开头。例如 `color-` 或 `space-`。如果有子类别，也应包含在命名中并用连字符分隔，例如：`color-primary-` 或 `color-secondary-`。
* **Element（元素）、Pattern（模式）和 Template（模板）：** 名称不带前缀，但*应该*与现有及未来的 HTML 元素兼容，_并且_以大写字母开头。

## 尺寸命名

Vue Design System（Vue 设计系统）使用以下约定：

* **默认值：** 默认单位始终称为 `medium (m)`。
* **小于默认值：** 当需要定义一个比 `medium` 更小的尺寸时，应命名为 `small (s)`、`x-small (xs)`、`xx-small (xxs)` 等。
* **大于默认值：** 当需要定义一个比 `medium` 更大的尺寸时，使用 `large (l)`、`x-large (xl)`、`xx-large (xxl)` 等。具体示例如下：

```
size_xxl:
  value: "64px"
size_xl:
  value: "48px"
size_l:
  value: "24px"
size_m:
  value: "16px"
size_s:
  value: "13px"
size_xs:
  value: "11px"
size_xxs:
  value: "8px"
```

## 颜色命名

Vue Design System 使用以下约定：

* **默认值：** 默认基础色始终称为 `color-{name}`。
* **深于默认值：** 当需要定义色阶（Shade）时，使用 `color-{name}-dark`、`color-{name}-darker` 或 `color-{name}-darkest`。
* **浅于默认值：** 当需要定义色调（Tint）时，使用 `color-{name}-light`、`color-{name}-lighter`、`color-{name}-lightest` 等。具体示例如下：

```
color_red_darker:
  value: "hsla(7, 83%, 33%, 1)"
color_red_dark:
  value: "hsla(7, 83%, 43%, 1)"
color_red:
  value: "hsla(7, 83%, 53%, 1)"
color_red_light:
  value: "hsla(7, 83%, 63%, 1)"
color_red_lighter:
  value: "hsla(7, 83%, 73%, 1)"
```

另请参阅[术语表](https://github.com/arielsalminen/vue-design-system/wiki/Terminology)，该部分与"事物的命名"密切相关。
