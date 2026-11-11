---
title: "Gradio 的離線行為：字型、使用分析、分享連結、公式（官方 repo 的文件與原始碼）"
type: doc
tier: A
fit: 中
topics: [T7]
year: 2026
venue: "gradio-app/gradio（★44k，Apache-2.0，最新 6.31.0，2026-10-28）；用 gh api 讀 guides/04_additional-features/10_environment-variables.md、gradio/themes/base.py、gradio/themes/utils/fonts.py、js/markdown-code/package.json"
url: https://github.com/gradio-app/gradio/blob/main/guides/04_additional-features/10_environment-variables.md
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

新版 Gradio 的預設字型已經是內建檔案、公式用打包好的 KaTeX，看起來可以離線；但**使用分析預設開啟**，要設 `GRADIO_ANALYTICS_ENABLED=False`，自訂主題也不要用 `GoogleFont`。

## 他們怎麼做（文件與原始碼說了什麼）

- **字型**：
  - `gradio/themes/base.py` 的預設字型是 `LocalFont("IBM Plex Sans")` 和 `LocalFont("IBM Plex Mono")`。
  - `LocalFont` 從 Gradio 自己的 `static/fonts` 載入；`GoogleFont` 則會產生 `fonts.googleapis.com` 的網址。
  - 也就是說，只有自訂主題選了 `GoogleFont` 才會對外連線（由原始碼推論）。
- **舊版的問題**：網路上有「離線時 Gradio 介面卡住」的回報，原因是舊版主題從 Google Fonts 抓字型（搜尋時看到 Stable Diffusion WebUI 的修正 commit 和 Hugging Face 論壇討論，只當線索）。新版預設已經不是這樣。
- **使用分析**：環境變數文件寫 `GRADIO_ANALYTICS_ENABLED` 預設是 `"True"`（文件的說明句子本身沒寫完）。
- **分享連結**：`GRADIO_SHARE` 預設 `"False"`；設成 True 才會建立公開網址，那需要網路。
- **公式**：前端 `js/markdown-code` 的依賴裡有 `katex`，表示 LaTeX 用打包進前端的 KaTeX 渲染，不是從 CDN 載入（由依賴清單推論）。GitHub 程式碼搜尋在 `js/` 底下只在官網原始碼 `js/_website` 找到 `cdn.jsdelivr.net`。

## 證據

- 只有文件與原始碼的靜態閱讀，沒有執行。`../.venv` 沒有安裝 Gradio（只有 `rich`），依規定不安裝，所以無法斷網實測。

## 對 AI TA：可以借用／不適用（原因）

- **可以借用**：
  - 用 Python 就能做出「聊天 + 測驗 + 顯示出處」的本機網頁，和專案的 Python 環境一致（推論）。
  - 能渲染公式，適合機器學習筆記；終端機做不到。
  - 啟動時固定設 `GRADIO_ANALYTICS_ENABLED=False`、不開 share、主題只用內建字型。
- **不適用／風險**：
  - 離線行為是讀原始碼推論的，要等開發階段安裝後斷網驗證。
  - 版本更新很快（6.x），升級後要重查有沒有新的對外連線。

## 限制與疑點

- 使用分析送出哪些資料、送到哪裡，這次沒有讀 `analytics.py`。
- KaTeX 是否完整打包進 PyPI 套件，要裝好後斷網確認。
