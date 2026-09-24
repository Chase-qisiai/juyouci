# 字幕来源备选

按已找到的单集链接选用，不必逐站走完。下列站点仅是候选，是否收录以本次核实为准。

- Springfield Springfield：可搜索 `剧名 SxxExx site:springfieldspringfield.co.uk`。单集路径通常为 `/view_episode_scripts.php?tv-show=show-slug&episode=s01e01`；slug 去除撇号等标点。
- subslikescript：搜索 `剧名 season 1 episode 1 site:subslikescript.com`。链接含剧集 ID 和集标题，从实际搜索结果/剧集页获取，不猜 URL。
- Forever Dreaming、剧集 Fandom transcript 页：作为替代来源，核对年份、剧名和集数。
- 正文提取工具无法读取时，可尝试公开页面直连或 `https://r.jina.ai/` + 原始 URL；需要交互时使用可用浏览器。不绕过访问权限，不假定某个代理永远可用。

curl 请求使用 `--connect-timeout 8 --max-time 20 -fL`。成功标准是剧集身份正确且含连续对话，不是 HTTP 200 或页面字数多。沿用 SKILL.md 的候选数量上限，不对同一个失败请求反复重试。
