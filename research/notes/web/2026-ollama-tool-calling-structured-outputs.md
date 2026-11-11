---
title: "Ollama 官方文件：工具呼叫、結構化輸出、思考模式（含本機 qwen3.5:9b 設定）"
type: doc
tier: A
fit: 高
topics: [T5, T4]
year: 2026
venue: "docs.ollama.com/capabilities（2026-11-11 讀取）；本機 Ollama 0.40.10 的 /api/show；ollama/ollama v0.40.10 原始碼"
url: https://docs.ollama.com/capabilities/tool-calling
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

Ollama 原生支援工具呼叫（單次、平行、多輪 agent 迴圈）、用 `format` 參數強制 JSON schema 的結構化輸出，以及可開關的思考模式。這些是 AI TA 自己寫 harness 時要直接用的 API。

## 他們怎麼做

- **工具呼叫**（[Tool calling](https://docs.ollama.com/capabilities/tool-calling)）：
  - `/api/chat` 傳 `tools`（JSON schema 描述的函式），模型回 `message.tool_calls`；應用程式執行後用 `role: "tool"` 把結果送回。
  - 支援單次、平行（一次回多個呼叫）、多輪 agent 迴圈（`while` 迴圈直到模型不再呼叫工具）、串流。
  - 文件建議：「告訴模型它在一個迴圈裡、可以呼叫多次工具」可能有幫助。
- **結構化輸出**（[Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs)）：
  - `format: "json"` 或 `format: <JSON schema>`；Python 可用 Pydantic 的 `model_json_schema()` 產生 schema，再用 `model_validate_json()` 驗證。
  - 官方建議：**也把 schema 以文字放進提示**來引導模型；把 temperature 調低（例如 0）讓結果更穩定。
  - OpenAI 相容 API 用 `response_format`。**Ollama 雲端目前不支援結構化輸出**（本機才有）。
- **思考模式**（[Thinking](https://docs.ollama.com/capabilities/thinking)）：`think: true/false` 或模型定義的等級；推理過程在 `message.thinking`，答案在 `message.content`，兩者分開。
- **本機 qwen3.5:9b 的實際設定**（`/api/show`，2026-11-11）：
  - 能力：completion、vision、tools、thinking；思考可設 `[false, true]`，**預設開啟**。
  - 9.7B 參數、nvfp4 量化、MLX runner；模型本身的上下文長度 262,144。
  - 預設取樣參數：temperature 1、top_p 0.95、top_k 20、presence_penalty 1.5（等於模型卡的「思考模式、一般任務」建議值）。
  - 提示格式不是用範本檔，而是 Ollama 內建的 `qwen3.5` renderer／parser（把訊息和工具轉成模型認得的格式，再把輸出解析回 `tool_calls`）。v0.40.10 原始碼（`model/renderers/qwen35.go`）中，工具呼叫格式是 XML 風格的 `<tool_call><function=...><parameter=...>`。
- **相關新能力（只記指標）**：Ollama 有「Decision／System One」端點，給文字和問題回傳是／否機率，可能用在批改；細節見 [T2 的嵌入模型筆記](2026-ollama-embedding-models.md)。

## 證據

- 官方文件，只說明「能做什麼」，沒有可靠度數字。
- 本機設定是我在 2026-11-11 用 `/api/show` 讀到的實際值。

## 對 AI TA：可以借用／不適用

- **可以借用**：
  - 自己寫 harness 只需要 `/api/chat` 的 `tools`、`format`、`think` 三個參數，不需要框架（推論）。
  - 出題、批改這種要給程式讀的輸出，用 `format` 加 schema，再用 Pydantic 驗證；schema 同時放進提示。
  - 思考模式可以按步驟開關：需要推理的步驟（解釋、判斷錯因）開，格式化或簡單分類關掉，省時間（推論；速度差異見 [本機實驗](../internal/2026-local-qwen35-tool-calling.md)）。
- **要注意**：
  - Ollama 的預設取樣是 temperature 1；工具呼叫和結構化輸出若要穩定，應在請求裡覆寫（官方建議結構化輸出用 0）。
  - 本機 `ollama ps` 顯示 qwen3.5:9b 的 CONTEXT 是 32768；我在 API 傳 `num_ctx: 65536` 後仍顯示 32768（見本機實驗）。
  - 社群回報 qwen3.5 在 Ollama 的工具呼叫曾有格式問題（[ollama#14493](https://github.com/ollama/ollama/issues/14493) 仍開著；[ollama#14745](https://github.com/ollama/ollama/issues/14745)「qwen3.5:9b 有時把工具呼叫印成文字」已關閉）。這些回報針對 0.17–0.30 版；0.40.10 的 renderer 已改用 XML 格式，但能不能完全解決要靠實測（C 級線索）。

## 限制與疑點

- 文件沒有版本號；內容以 2026-11-11 讀取為準。工具類資料變動快。
- 結構化輸出開啟思考模式時，schema 只約束 `content` 還是也影響思考，文件沒寫；本機實驗有測。
