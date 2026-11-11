---
title: media-note 筆記格式（reading-v3）與查證規範
type: internal
tier: internal
fit: 高
topics: [T2, T3, T7]
year: 2026
venue: "自己的 skill：~/.claude/skills/media-note（v3.4.0）"
url: ~/.claude/skills/media-note/references/note-format.md
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

用 media-note 產生的課程筆記有固定的結構，AI TA 可以直接拿這個結構來切段、引用講義頁和出題；回答也可以沿用同一套寫法。

## 筆記長什麼樣（reading-v3）

- **屬性區**：有 `note_style: reading-v3`、`generator: media-note`，可以用來辨認格式。
- **開頭**：依序是 `> [!abstract] 一分鐘看完`（300–500 字的摘要）、導讀表格、摺疊的來源、總覽圖。
- **正文三層**：H2 是主題，H3 是問題小節（標題是問句），H4 是子主題。
- **每個問題小節**：最多一句 `==螢光==` 標出結論，結尾放一個 `> [!tip] 這節記住`，用 1–2 句寫結論和成立條件。
- **講義引用**：用可以點的 PDF 頁面連結，例如 `[[Week3/課程 PPT/1. Regression.pdf#page=25|迴歸講義 p.25]]`。
- **術語**：第一次出現時寫成 `**中文**（English，縮寫；白話）`。
- **結尾**：`## 自我檢查`，答案用 `> [!question]-` 摺疊起來（選配）。

## 對 AI TA 的意義（推論，待 T2、T3、T7 驗證）

- **切段（T2）**：以 H3 問題小節為單位切段。標題本身就是一個問題，和提問的方式接近，可能比固定字數切段更好檢索。
- **出處（T2）**：段落裡的講義頁連結可以直接當引用，回答能附上「迴歸講義 p.25」並點過去。
- **出題（T3）**：
  - 「這節記住」和螢光句是每節最該記住的結論，適合當出題重點。
  - 「自我檢查」本身就是題目加答案，可以當題庫和評估題。
- **閃卡（T3）**：固定格式的術語定義，可以自動整理成閃卡。
- **回答格式（T7）**：AI TA 的回答沿用同一套寫法，包括白話推理、術語格式、「這節記住」，讀起來就和課程筆記一致。

## 查證規範（research-policy）

研究規範的來源分級和主張分類沿用這份規範，對應方式見 [research/README.md](../../README.md) 第 3 節。

## 限制與疑點

- 不是每份課程筆記都是 reading-v3。舊筆記用時間軸格式（course-format），`Midterm Review/` 可能又是另一種格式，T2 要先盤點。
- 上面的好處都是推論，要在評估題組上實測。
