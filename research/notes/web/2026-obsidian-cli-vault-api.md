---
title: "Obsidian 官方文件：CLI 與 Vault API（外部程式怎麼讀筆記的原始 Markdown）"
type: doc
tier: A
fit: 高
topics: [T7, T2]
year: 2026
venue: "Obsidian 官方說明「Obsidian CLI」（obsidianmd/obsidian-help repo）與開發者文件「Vault」（obsidianmd/obsidian-developer-docs repo），用 gh api 讀原文；本機 Obsidian 1.12.7"
url: https://github.com/obsidianmd/obsidian-help/blob/master/en/Extending%20Obsidian/Obsidian%20CLI.md
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

Obsidian 的 vault 就是一個裝 `.md` 檔的資料夾：外掛透過 Vault API 讀到的是原始 Markdown，官方 CLI（1.12.7 起）也能 `read`、`search`。所以 AI TA 可以直接讀筆記原檔，公式（`$...$`）不會像從閱讀畫面複製那樣消失。

## 他們怎麼做（文件說了什麼）

- **Vault API**（[Vault](https://github.com/obsidianmd/obsidian-developer-docs/blob/main/en/Plugins/Vault.md)，網站版在 docs.obsidian.md）：
  - 「vault 由一個資料夾和它的子資料夾組成」。
  - `vault.read()`、`vault.cachedRead()` 回傳檔案內容（原始文字）。只想顯示就用 `cachedRead()`；要改寫再存回就用 `read()`，避免蓋掉別人剛改的內容。
  - Vault API 只看得到 App 裡可見的檔案；隱藏資料夾要用 Adapter API。
- **CLI**（網站版在 obsidian.md/help/cli）：
  - 需要 Obsidian 1.12 安裝版（1.12.7 以上），在設定 → 一般裡開啟並註冊。
  - **Obsidian App 必須在執行**；沒開的話，第一個指令會自動啟動 App。CLI 是在遙控執行中的 App。
  - `obsidian read file=<名稱>` 或 `path=<路徑>`：讀檔案內容。
  - `obsidian search query=...`：回傳符合的檔案路徑；`search:context` 回傳「路徑:行號: 內容」的 grep 格式；兩者都能輸出 JSON。
  - 用 `vault=<名稱>` 指定 vault；另有查詢 Bases 的 `base:query` 等指令。
  - 想在沒有桌面 App 的情況下同步，官方另有 Headless Sync（本次沒讀）。
- **本機**：`/Applications/Obsidian.app` 是 1.12.7，`/usr/local/bin/obsidian` 已存在（只看檔案，沒有執行 CLI）。

## 證據

- 這是官方文件，證明的是「工具提供什麼介面」。原始 Markdown 會保留公式這點，由基準紀錄的對照佐證：課程筆記原檔裡的公式是 LaTeX 原文（見 [ollama-app-baseline](../internal/ollama-app-baseline.md)）。

## 對 AI TA：可以借用／不適用（原因）

- **可以借用**：
  - **最簡單的做法：直接讀 vault 資料夾裡的 `.md` 檔**。不需要 Obsidian 在執行，也不需要外掛；公式、`==螢光==`、callout、講義頁連結都完整保留（推論，依「vault 就是資料夾」）。這直接解決基準紀錄的「複製遺失公式」問題。
  - **想在 Obsidian 裡用**（例如側邊欄聊天），就寫外掛，用 Vault API 讀同一份原始 Markdown。
  - **CLI 的 `search:context`** 可以當簡單的關鍵字檢索備案，或讓人在終端機快速查筆記（推論）。
- **不適用**：
  - CLI 依賴 App 在執行，不適合當 AI TA 讀資料的唯一方式。

## 限制與疑點

- 依規定沒有執行 `obsidian` CLI，所以不確定 `read` 的輸出是否包含 frontmatter 屬性區。
- 直接讀資料夾會繞過 Obsidian 的連結解析：像 `[[Week3/課程 PPT/1. Regression.pdf#page=25|迴歸講義 p.25]]` 這種 wikilink，要自己解析成檔案路徑和頁碼（T2）。
