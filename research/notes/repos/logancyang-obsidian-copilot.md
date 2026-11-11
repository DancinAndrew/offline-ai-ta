---
title: Copilot for Obsidian
type: repo
tier: B
fit: 中
topics: [T7, T4]
year: 2026
venue: "logancyang/obsidian-copilot；GitHub ★8.0k；最後 push 2026-11-11；AGPL-3.0"
url: https://github.com/logancyang/obsidian-copilot
self_reported: true
status: read
accessed: 2026-11-11
---
## 一句話

README 自稱是下載量最高的 Obsidian AI 外掛，現在已經變成「在 Obsidian 裡跑 agent」的平台（後端可以接 OpenCode、Claude Code、Codex 等）。用本機模型或自己的 API key 不必付費，但代管模型和部分工具走開發公司 Brevilabs 的雲端。

## 他們怎麼做（README 說了什麼，2026-11-11）

- **三種模型來源**：
  - Copilot 代管的模型（付費）。
  - **BYOK**（bring your own key，自帶金鑰）：填自己的雲端、本機或 OpenAI 相容端點。金鑰存在本機的 Obsidian Keychain，不寫進 vault。
  - 透過 OpenCode 路由的模型。README 警告免費的 OpenCode Zen 模型可能記錄或拿提示訓練。
- **免費範圍**：用自己的 agent 帳號、金鑰或本機模型時不需要授權。免費功能包含一般 Agent 對話、以 Markdown 為脈絡的 Projects、自訂 Skills 和 Commands、Quick Chat、Quick Ask、本機的 Miyo 搜尋。
- **付費範圍**：代管模型、雲端工具、多 agent、預覽功能（需要 Believer 或 Supporter 授權）。
- **隱私**：筆記留在 vault，本機的 Miyo 索引留在裝置上；提示和附上的筆記內容會送到你選的模型；用代管功能時會送到 Brevilabs。
- **Agent 只在桌面版**，因為後端要跑本機程序。

## 證據

- 只有 README 的自我描述，沒有使用成效或獨立評測。

## 對 AI TA：可以借用／不適用（原因）

- **可以借用**：
  - 想在 Obsidian 裡跟筆記對話時，它可以接 Ollama 的 OpenAI 相容端點，免費就能用（依 README，未實測）。
  - 「Projects 以 Markdown 為脈絡」顯示一個方向：直接把筆記原文當上下文，而不是複製貼上。
- **不適用**：
  - 功能多、變動快，提示詞和流程由外掛決定，無法精準控制送給 9B 模型的系統提示和工具數量（T5 的疑慮）。
  - 很難拿它做「裸模型 vs AI TA vs frontier」的可重現評估（推論）。
  - AGPL 授權：只當自己的工具沒問題；若要把它的程式碼改寫進公開 repo，要遵守 AGPL（推論）。

## 限制與疑點

- 沒有安裝實測，也沒確認斷網時哪些功能會壞。
- 本機 Miyo 搜尋用什麼嵌入模型、第一次使用是否要下載，README 沒寫。
