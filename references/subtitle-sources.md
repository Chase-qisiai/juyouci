# 字幕来源参考

改编自 https://github.com/pyang5166/gbro-series-vocab 。下列站点行为是上游经验，可能变化；以本次获取的剧名、集数和正文核实结果为准。获取失败时使用可用的浏览器工具，不得绕过访问权限。



按顺序尝试，找到即停止。

### 方法 A：Springfield Springfield（老剧首选）

slug 规则：剧名转小写，空格换连字符，**去掉所有非字母数字和连字符的字符**（撇号、冒号、逗号、句点等），连续连字符合并为一个。例如 `Grey's Anatomy` → `greys-anatomy`，`It's Always Sunny in Philadelphia` → `its-always-sunny-in-philadelphia`。

```bash
SHOW_SLUG=$(echo "Grey's Anatomy" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | sed -E 's/[^a-z0-9-]//g; s/-+/-/g')
curl -sL "https://r.jina.ai/https://www.springfieldspringfield.co.uk/view_episode_scripts.php?tv-show=${SHOW_SLUG}&episode=s02e03"
```

**判断成功（两条必须同时满足）**：
1. 页面标题含剧名（找不到该剧时网站返回的错误页标题只有集数没有剧名，且正文只剩导航链接，长度也可能上万字符——不要只看长度）
2. 正文含大量对话行（连续的口语句子），而非以 `[链接](url)` 为主的导航内容

**注意**：Springfield 已基本停更，2023 年后的新剧（如 The Pitt、Severance、White Lotus S3）都没有收录。方法 A 失败一次就果断转方法 B，不要反复试。

### 方法 B：subslikescript 站内搜索（新剧首选）

subslikescript 持续收录新剧，但直接 curl 会被 JS 验证码挡住，**每一步都必须经 r.jina.ai 抓取**。三步走：

```bash
# 1. 站内搜索，拿剧集页 URL（形如 /series/{Name}-{id}）
curl -sL "https://r.jina.ai/https://subslikescript.com/search?q={关键词}"

# 2. 抓剧集页，找目标集链接（形如 /series/{Name}-{id}/season-{s}/episode-{e}-{集标题}）
#    单集 URL 末尾带集标题，无法直接拼出，必须从剧集页拿
curl -sL "https://r.jina.ai/https://subslikescript.com/series/{Name}-{id}"

# 3. 抓单集正文
curl -sL "https://r.jina.ai/{单集URL}"
```

坑（实测）：
- 搜索是按词匹配的，全名可能搜不到：`The Pitt` 无结果，搜 `Pitt` 才命中。失败时去掉 The/标点，用剧名里最独特的一个词重搜
- 从 markdown 链接里抽出的 URL 可能带尾部空格，拼给 r.jina.ai 前先修剪，否则返回空
- 同名剧按年份区分（如 Severance 1988 vs 2022–…），选年份对的那个

### 方法 C：通用 WebSearch

`"{剧名}" "S{xx}E{xx}" transcript script site:transcripts.foreverdreaming.org OR site:subslikescript.com OR site:springfieldspringfield.co.uk`

剧集的 Fandom Wiki transcript 页也是可靠来源。

### 方法 D：直连兜底（r.jina.ai 不可用时，仅限 Springfield）

如果 r.jina.ai 超时或限流，直接 curl Springfield 原始页面并本地清洗：

```bash
# 注意起点必须匹配 class="scrolling-script-container"（带 class=）——
# 裸的 scrolling-script-container 会先命中页面内联 CSS，抓到样式表
curl -sL "https://www.springfieldspringfield.co.uk/view_episode_scripts.php?tv-show=${SHOW_SLUG}&episode=s02e03" \
  | sed -n '/class="scrolling-script-container"/,/<\/div>/p' \
  | sed -E 's/<br>/\n/g; s/<[^>]+>//g' \
  | sed '/^[[:space:]]*$/d'
```

### 找不到时

告诉用户：「未找到《{剧名}》第{season}季第{episode}集的字幕，请从网上复制剧本文字后发给我，我继续处理。」

---

