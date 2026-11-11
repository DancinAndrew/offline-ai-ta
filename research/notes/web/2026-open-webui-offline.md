---
title: "Open WebUI 離線模式（官方文件站：離線教學與環境變數參考）"
type: doc
tier: A
fit: 中
topics: [T7, T2]
year: 2026
venue: "docs.openwebui.com（2026-11-11 讀取）；Open WebUI v0.13.3（2026-11-08）；GitHub ★158k，最後 push 2026-11-11，自訂授權（GitHub 顯示 NOASSERTION）"
url: https://docs.openwebui.com/tutorials/maintenance/offline-mode.md
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

Open WebUI 是功能最完整的本機網頁聊天介面，可以離線使用，但要先在有網路時把嵌入模型等快取好；`OFFLINE_MODE` 只關掉更新檢查和模型下載，**不會擋住其他對外連線**，真正隔離要靠防火牆或斷網。

## 他們怎麼做（文件說了什麼）

- **離線前要準備的東西**（離線教學）：本機推論服務（例如 Ollama）、**嵌入模型**（embedding model：把文字轉成向量，用來找相關段落）、文件抽取、（有用的話）重排序與語音模型，以及離線也能用的登入方式。
- **`OFFLINE_MODE=true` 會關掉**（[環境變數參考](https://docs.openwebui.com/reference/env-configuration.md)，官方）：
  - 版本更新檢查與 UI 的更新通知。
  - 從 Hugging Face 下載嵌入模型。
  - 嵌入、重排序、Whisper 模型的自動更新。
  - 外掛宣告的 Python 套件自動安裝。
- **`OFFLINE_MODE` 仍會運作的**：外部 LLM API 連線、OAuth 登入、外部 web search 與 RAG API。
- **新安裝直接開離線模式的陷阱**：程式可以啟動，但第一次上傳文件或檢索時出現 `No embedding model is loaded`。要先連網跑一次，讓模型快取。
- **網路隔離**：文件明說這些變數「不會阻擋對外連線」，要另外用防火牆、容器內部網路或實體斷網。
- **離線驗收步驟**：斷網後重啟 → 一般聊天 → 上傳一份含獨特事實的小文件 → 問那個事實 → 另外確認網路真的被擋。
- **登入**：預設要建立帳號。單人可設 `WEBUI_AUTH=False`（快速入門頁），但設了之後不能再切回多人模式。
- **預設嵌入模型範例**：`sentence-transformers/all-MiniLM-L6-v2`（英文模型）。

## 證據

- 這是工具自己的文件，只能證明「它宣稱能做什麼、要怎麼設定」，不是使用成效。
- 離線教學頁本身標明「社群貢獻，Open WebUI 團隊不支援」；上面關於 `OFFLINE_MODE` 的行為取自官方的環境變數參考頁。

## 對 AI TA：可以借用／不適用（原因）

- **可以借用**：
  - **它的離線驗收步驟**可以直接改成 AI TA 第 5 步「斷網能跑」的檢查清單。
  - **提醒**：「介面在本機」不等於「整條流程在本機」。模型、嵌入、文件抽取每個元件都要各自確認。
- **不適用／風險**：
  - 內建的切段和引用格式是通用設計，不認得 media-note 的 H3 小節和講義頁連結；要客製就得改它的程式或繞過它（推論）。
  - 預設嵌入模型是英文的，中文筆記要換模型（T2）。
  - 功能很多（多人帳號、權限、工具、語音），對單人複習太重；也很難精確控制送給 9B 模型的系統提示（推論，T5）。
  - 通常用 Docker 或 pip 安裝；本研究階段依規定不安裝，所以沒有實測。

## 限制與疑點

- 沒有本機實測。
- 授權是自訂條款，本次沒有細讀；如果要在公開 repo 裡打包或修改品牌，要先查。
