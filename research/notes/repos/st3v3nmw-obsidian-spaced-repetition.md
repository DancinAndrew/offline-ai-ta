---
title: Obsidian Spaced Repetition 外掛
type: repo
tier: B
fit: 中
topics: [T7, T3]
year: 2026
venue: "st3v3nmw/obsidian-spaced-repetition；GitHub ★2.6k；最後 push 2026-11-01；MIT；最新 release 1.15.4（2026-06-14）"
url: https://github.com/st3v3nmw/obsidian-spaced-repetition
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

在 Obsidian 筆記裡直接寫閃卡（例如 `問題::答案`，或把 `==螢光==` 當挖空），在 Obsidian 內複習；1.15.0 起可以選 FSRS。缺點是**排程資料會寫回筆記本身**，每張卡後面多一行 HTML 註解。

## 他們怎麼做（架構、資料）

- **卡片語法**（README）：
  - 單行 `問題::答案`；雙向 `問題:::答案`；多行用 `?` 或 `??` 分隔問題與答案。
  - **挖空卡**（cloze：把句子裡的關鍵字遮起來讓你填）可以用 `==螢光==`、`**粗體**`、`{{大括號}}` 或自訂樣式。
  - 支援圖片、音訊、LaTeX、程式碼高亮（沿用 Obsidian 的渲染）。
- **牌組**：在筆記加 `#flashcards` 或 `#flashcards/子牌組` 標籤，或用資料夾結構。
- **脈絡標題**：卡片自動帶出「筆記名 > 標題 1 > 子標題」。
- **複習模式**：依排程複習到期的卡；或「cram」不管排程全部複習；也能複習整篇筆記。
- **排程資料存哪裡**（docs/data-storage）：
  - 卡片：複習後在下一行加上 `<!--SR:!2024-08-16,51,230-->` 這種註解（也可以設定放在同一行）。
  - 整篇筆記：寫在 frontmatter 的 `sr-due`、`sr-interval`、`sr-ease`。
  - 「所有排程存在一個獨立檔案」還沒實作（issue #162）。
- **演算法**：預設是 SM-2 的變體（SM-2-OSR）。release 1.15.0（2026-05-24）說 FSRS「終於可用，但不預設開啟，可能還有 bug」。

## 證據

- 官方文件的演算法頁仍寫 FSRS 是「Planned」，而且自承很久沒更新；README 和 1.15.0 的 release notes 則說已經支援。**兩者矛盾，以日期較新的 release notes 為準**。
- 沒有使用成效數據；星數和更新頻率只代表專案活躍。

## 對 AI TA：可以借用／不適用（原因）

- **可以借用**：
  - media-note 每個 H3 小節最多一句 `==螢光==` 結論，剛好能變成挖空卡；加上「筆記 > H2 > H3」的脈絡標題，就是現成的閃卡（推論）。
  - 如果使用者想留在 Obsidian 裡複習，這個外掛已經有完整的閃卡介面，AI TA 只要負責產生卡片文字（推論）。
- **不適用／風險**：
  - 排程寫進筆記，會改動課程筆記原檔；AI TA 讀筆記時也會讀到一堆 `<!--SR:...-->` 雜訊（推論）。若要用，閃卡應該寫在另外的檔案，不寫在課程筆記裡。
  - 只解析加了 `#flashcards` 標籤的筆記，現有筆記要加標籤才會生效。

## 限制與疑點

- 沒有安裝實測。
- FSRS 才剛加入（1.15.x），穩定度未知。
