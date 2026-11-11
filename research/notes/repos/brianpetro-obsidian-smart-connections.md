---
title: Smart Connections（Obsidian 外掛）
type: repo
tier: B
fit: 低
topics: [T7, T2]
year: 2026
venue: "brianpetro/obsidian-smart-connections；GitHub ★5.6k；最後 push 2026-10-10；Smart Plugins License（source-available，不是 OSI 認可的開源授權）"
url: https://github.com/brianpetro/obsidian-smart-connections
self_reported: true
status: read
accessed: 2026-11-11
---
## 一句話

v4 起核心外掛只做「找相關筆記」：內建本機嵌入模型，宣稱預設私密且離線；聊天功能拆到另一個外掛，而且**接 API 模型（包含本機 Ollama）的功能放在付費的 Smart Chat Pro**。

## 他們怎麼做（README 說了什麼）

- **核心功能**：安裝後用內建的本機**嵌入模型**（把文字轉成向量，用來比對意思相近的筆記）幫 vault 建索引，在側欄顯示和目前筆記語意相近的筆記。README 說「不需要額外 App、CLI 或 API key」「Private and offline by default」。
- **聊天**：Smart Chat 已經從 Smart Connections 拆成獨立外掛；所有以 API 連線的模型整合（雲端和本機）都移到 Smart Chat Pro。
- **Pro**：提供給專案贊助者。
- **授權**：source-available，可以使用、修改、再散布，但限制做「通用的、與它競爭的 Obsidian 產品」。

## 證據

- 只有 README 的自我描述。

## 對 AI TA：可以借用／不適用（原因）

- **可以借用**：
  - 「寫筆記時自動顯示相關筆記」是一種被動的複習提示，可以當介面靈感（推論）。
- **不適用**：
  - 要用 Ollama 對話得付費，而且核心功能是找相關筆記，不是問答、出題、批改。
  - 內建嵌入模型叫什麼、支不支援中文、第一次使用要不要下載，README 沒寫，所以「離線」的宣稱未驗證。

## 限制與疑點

- 沒有安裝實測。
