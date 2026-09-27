# 词库数据与通用学习器

## 单集词库数据

每集先整理为一个 deck 对象，再合并到学习器的 `decks` 列表：

```json
{
  "title": "剧名 S01E01 · 词汇学习",
  "deck_id": "show-slug:S01E01:zh",
  "sources": ["真实来源 URL 或用户提供的字幕文件名称"],
  "note": "可选说明，例如材料不足，仅提取 32 条。",
  "cards": [
    {
      "term": "词汇或短语",
      "answers": ["可接受的标准拼写", "可接受的常见变体"],
      "meaning": "本句语境中的中文释义",
      "ipa": "/音标/",
      "sentence": "实际来源中的英文原句",
      "translation": "原句的中文译文",
      "targets": ["原句中的实际词形"]
    }
  ]
}
```

`title` 和 `deck_id` 必填；`sources` 必须是字符串数组；`cards` 接受 1–500 条。每张卡的 `term`、`meaning`、`ipa`、`sentence`、`translation` 都是非空纯文本，不放 HTML 标记。`answers` 和 `targets` 可省略，必须是非空字符串数组；省略时分别默认为 `[term]` 和 `[term]`。只把语义正确、拼写确实可接受的形式放入 `answers`。

`deck_id` 对一个剧集及语言必须稳定，例如 `show-slug:S01E01:zh`。更新同一集时沿用原 ID，不要因标题、字幕来源或词条顺序变化而另建重复 deck。同 ID 导入表示更新该集：元信息和卡片列表采用新版本；同 ID 词条保留已有进度，新加入或身份变化的词条从未学习开始。其他剧集 deck 与进度不变。

不要手工填写卡片 `id` 或 `target_spans`。生成/合并工具根据词头与规范化原句生成稳定 ID，并计算目标片段位置；HTML 页面用这些位置显示高亮和挖空。原句中实际形式与词头不同时，`targets` 必填，例如 `term` 为 `figure out`、原句为 `She figured it out.` 时可设为 `["figured", "out"]`。目标片段必须按原样出现在原句中，不能改原句迁就词头；目标片段不能重叠。

## 内嵌词库集合

通用学习器把完整词库集合嵌入一个 application/json 脚本节点。模板只使用此占位约定：

```html
<script type="application/json" id="vocab-library">__VOCAB_LIBRARY__</script>
```

生成后的占位符必须替换为一个有效 JSON 对象，根形状如下：

```json
{
  "schema_version": 1,
  "decks": [
    {
      "title": "剧名 S01E01 · 词汇学习",
      "deck_id": "show-slug:S01E01:zh",
      "cards": [],
      "sources": [],
      "note": ""
    }
  ]
}
```

集合内每个 deck 使用上面的单集词库结构。首次创建学习器时，`decks` 至少包含本次首集词库；不可生成空库。后续只向集合新增或替换 deck，然后把完整集合安全写回固定母版 HTML。对 JSON 做安全序列化，避免词条中的 `</script>`、`<`、`>`、`&`、U+2028 或 U+2029 破坏内嵌数据；页面以 `textContent` 等安全方式渲染用户字幕文本。

## 词库、进度和偏好边界

`juyouci.html` 保存完整 `vocab-library`，复制 HTML 文件即可备份全部词库。练习进度以 `deck_id` 和词条 `id` 为键分开保存，翻卡自评/输入回忆的选择是通用学习器的浏览器偏好，对全部 deck 生效。页面进度备份保存浏览器学习状态，不包含词库正文；HTML 备份也不包含浏览器进度或偏好。完整迁移时同时保留 HTML 文件和页面导出的进度备份。更换浏览器、设备或移动文件后，本地存储可能无法自动跟随。

## 文件处理规则

- 固定母版路径为 `~/Documents/series-vocab/juyouci.html`。首次创建时从技能模板生成学习器并放入首集词库；后续新增/更新一集时，必须读取现有文件、保留其他 deck 并合并回同一文件。
- 如果既有母版不存在、不可读、损坏，或当前 Agent 看不到，不要创建空库或只包含新集的替代文件。向用户索要现有 HTML 的路径或文件后再继续。
- 普通使用最终交付更新后的 HTML 并说明加入的剧集及词条数。单集 JSON 是中间数据，不需单独交付；除非用户明确要求数据包。
- 不分发整集字幕，只把精选且真实来源可核实的学习例句放入 cards。
