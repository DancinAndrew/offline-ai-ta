---
title: "Qwen-Agent（Qwen 官方 agent 框架）與 Qwen 官方函式呼叫文件"
type: repo
tier: A
fit: 中
topics: [T4, T5]
year: 2026
venue: "QwenLM/Qwen-Agent；GitHub ★ 17.3k；最後推送 2026-03-04；Apache-2.0；Qwen 官方。另讀 qwen.readthedocs.io 的 Function Calling 頁"
url: https://github.com/QwenLM/Qwen-Agent
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

Qwen 官方的 agent 框架，模型卡推薦用它做 Qwen3.5 的 agent；它能接 Ollama 的 OpenAI 相容端點、有函式呼叫、MCP、RAG、Gradio 介面。官方文件同時坦承：**再好的提示或範本也不能保證模型每次都照工具呼叫格式輸出**，程式要準備好壞掉時的補救。

## 他們怎麼做

- **元件**（README）：LLM 類別（內建函式呼叫）、Tool 類別、Agent 類別（例如 `Assistant`）；`WebUI(bot).run()` 一行開 Gradio 介面。
- **接模型**：`model_server` 指向任何 OpenAI 相容 API（README 明寫 vLLM 或 Ollama）。
- **函式呼叫範本**：預設 `nous`（Hermes 風格，`<tool_call>` 標籤），README 說推薦給 Qwen3；支援平行呼叫；解析時刻意不在思考段落裡找 `<tool_call>`。
- **Qwen3.5 的官方範例**（`examples/assistant_qwen3.5.py`）：設 `use_raw_api: True`，也就是交給推論服務（vLLM／SGLang）的原生工具解析，而不是 Qwen-Agent 自己的範本；工具用 MCP 設定檔接（範例用 `uvx`、`npx` 啟動 MCP 伺服器）。
- **其他功能**：長文件問答的 RAG 範例、程式碼直譯器（跑在本機 Docker；README 說只有基本隔離，正式環境要小心；Math 範例的 Python 執行器「沒有沙箱」）。
- **官方函式呼叫文件**（[qwen.readthedocs.io](https://qwen.readthedocs.io/en/latest/framework/function_call.html)，以 Qwen3 為例）：
  - 推薦 Hermes 風格的工具呼叫格式；Qwen-Agent 是「Qwen3 函式呼叫的標準實作」。
  - 對 Qwen3 這類推理模型，**不建議**用 ReAct 這種靠停止詞的範本，因為模型可能在思考段落輸出停止詞。
  - 結語：「即使提示和範本正確，也不保證模型生成永遠遵守協定……正式程式要準備好它壞掉時的對策」；「最終的解法是用自己的資料微調」。

## 證據

- 官方 repo 與文件，只說明能做什麼；沒有可靠度數字。
- 維護狀況：最後推送 2026-03-04（讀取時約 8 個月前）；Qwen3.5 支援在 2026-02-16 加入。

## 對 AI TA：可以借用／不適用

（評估標準：離線、提示負擔、能否改成複習流程、授權）

| 標準 | 評估 |
|---|---|
| 完全離線 | 模型可接本機 Ollama；但 MCP 範例要 `uvx`／`npx` 第一次下載伺服器，程式碼直譯器要 Docker 映像檔。只用自訂 Python 工具就能離線（推論） |
| 提示負擔 | 框架本身的工具範本短；負擔主要看自己放幾個工具（未量測） |
| 改成複習流程 | 可以：自訂 Tool 類別、自己寫 Agent 子類別控制流程；Gradio 介面可直接用 |
| 授權 | Apache-2.0 |

- **可以借用**：
  - 官方「不保證遵守格式」的提醒，直接支持 AI TA 要有驗證與重試層（Pydantic 驗證 JSON、工具名與參數白名單）。
  - 不要用停止詞式的 ReAct 範本，用模型原生的工具呼叫格式。
  - 想要現成介面時，`WebUI` 是一條快速路徑（介面另見 T7）。
- **不適用／要注意**：
  - 對 Qwen3.5，官方範例走 `use_raw_api`，工具解析其實交給 Ollama 的 qwen3.5 parser；所以 Qwen-Agent 不會修好 Ollama 那層的解析問題（推論）。
  - 我的核心流程只需要 `/api/chat` 的 tools 與 format，加一個框架的好處主要是介面和 MCP；如果流程由程式控制，框架帶來的抽象層可能比好處多（推論，與 [Anthropic 的建議](../web/2024-anthropic-building-effective-agents.md) 一致）。
  - 近 8 個月沒有推送，不符合研究規範 B 級「近半年有更新」的條件；作為官方資料仍是 A 級，但長期維護有風險。

## 限制與疑點

- 我沒有安裝或執行 Qwen-Agent（研究規則禁止安裝），上述都是讀 README、範例與文件得來。
- Qwen 官方函式呼叫文件以 Qwen3 為例，沒有 Qwen3.5 專屬段落；Qwen3.5 改用 Qwen3-Coder 式的 XML 工具格式（見 [模型卡筆記](../web/2026-qwen35-9b-model-card.md)），文件中「推薦 Hermes 風格」這點對 Qwen3.5 可能已不適用（推論）。
