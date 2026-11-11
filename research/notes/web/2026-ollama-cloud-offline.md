---
title: "Ollama 官方文件：雲端功能、web search 與離線使用（加本機檢查）"
type: doc
tier: A
fit: 高
topics: [T7, T4]
year: 2026
venue: "docs.ollama.com 的 FAQ、Cloud、Web search、macOS 頁（2026-11-11 讀取）；本機 Ollama 0.40.10"
url: https://docs.ollama.com/faq.md
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

Ollama 在本機推論不需要網路，但**雲端模型和 web search 預設是開著的**；官方提供 `OLLAMA_NO_CLOUD=1` 或 `server.json` 一個設定就能關掉。本機檢查確認，這台機器目前的雲端功能是開著的。

## 他們怎麼做（官方文件說了什麼）

- **本機推論**：FAQ 說，本機執行時「我們看不到你的提示或資料」；API 預設只綁 `127.0.0.1:11434`。
- **雲端模型**（[Cloud](https://docs.ollama.com/cloud.md)）：
  - 雲端模型不需要下載，但要登入 Ollama 帳號；在 App 或 CLI 裡用 `:cloud` 結尾的名稱（例如 `gemma4:cloud`）。
  - 頁面最後直接連到「只想用本機模型就關掉雲端功能」。
- **Web search**（[Web search](https://docs.ollama.com/capabilities/web-search.md)）：是 `https://ollama.com/api/web_search` 的雲端 API，需要免費帳號與 API key。
- **關掉雲端功能**（FAQ「How do I disable Ollama's cloud features?」）：
  - 在 `~/.ollama/server.json` 設 `{"disable_ollama_cloud": true}`，或設環境變數 `OLLAMA_NO_CLOUD=1`。
  - 重啟後 log 會顯示 `Ollama cloud disabled: true`。
  - 關掉之後，雲端模型和 web search 都不能用。
- **更新**（FAQ）：macOS 版會自動下載更新，按「Restart to update」才套用。
- **macOS App**（[macOS](https://docs.ollama.com/macos.md)）：App 是 GUI，CLI 在 `Ollama.app/Contents/Resources/ollama`；GUI 的 log 在 `app.log`。

## 證據（本機檢查，2026-11-11）

只讀設定和 log，並用 curl 呼叫本機 API，沒有改任何設定：

- `GET /api/version` 回 `0.40.10`；`GET /api/tags` 只有 `qwen3.5:9b`（約 7.6 GB，`runner: mlx`，能力標示 completion、vision、tools、thinking）。
- 沒有 `~/.ollama/server.json`，shell 也沒有設定 `OLLAMA_NO_CLOUD`。
- server log 記錄的設定是 `OLLAMA_NO_CLOUD:false`、`OLLAMA_REMOTES:[ollama.com]`，並印出 `Ollama cloud disabled: false`。
- App 的 log 有多次呼叫本機 `/api/v1/cloud` 的紀錄，表示 App 會查詢雲端功能的狀態。

## 對 AI TA：可以借用／不適用（原因）

- **可以借用**：
  - **AI TA 直接呼叫本機 API**，不經過 Ollama App 的聊天畫面，就不會碰到 App 內建的雲端功能（推論）。
  - **把「完全離線」寫成啟動檢查**：確認 `OLLAMA_NO_CLOUD=1`（或 server.json），並且只允許本機模型名稱，避免誤選 `:cloud` 模型（推論）。
  - **回應基準紀錄的疑點**：基準紀錄懷疑「App 預設提供搜尋工具」。官方文件確認 web search 是需要帳號的雲端功能，而雲端功能預設開著；但 App 聊天時會不會把搜尋工具的說明放進提示，文件沒寫，仍待驗證。
- **不適用／注意**：
  - 自動更新在離線時不會發生，也不影響推論；但評估期間最好固定版本，免得更新改變行為（推論）。

## 限制與疑點

- 沒有實際切換 `OLLAMA_NO_CLOUD` 測試，因為會重啟其他平行工作階段正在用的 Ollama 服務。
- 沒有斷網實測 App，「App 斷網時是否仍嘗試連線」未驗證。
- 工具類資料，超過一年要重查；0.40.10 是 2026 年的版本。
