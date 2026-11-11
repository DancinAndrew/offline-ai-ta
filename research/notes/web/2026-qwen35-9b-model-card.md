---
title: "Qwen3.5-9B 官方模型卡（Hugging Face）"
type: doc
tier: A
fit: 高
topics: [T5, T4]
year: 2026
venue: "huggingface.co/Qwen/Qwen3.5-9B（README，2026-11-11 讀取）；Apache-2.0"
url: https://huggingface.co/Qwen/Qwen3.5-9B
self_reported: true
status: read
accessed: 2026-11-11
---
## 一句話

官方說 Qwen3.5-9B「擅長工具呼叫」，自測 BFCL-V4 66.1、TAU2-Bench 79.1，並建議用 Qwen-Agent 或 Qwen Code 做 agent；但模型卡也建議思考模式要保留 128K 以上上下文，這和本機 Ollama 預設的 32k 有落差。

## 他們怎麼做

- **基本規格**：Apache-2.0；原生上下文 262,144 token，可延伸到約 101 萬。
- **思考模式**：預設先輸出 `<think>…</think>` 再回答；可以關掉直接回答。
- **上下文建議**：「Qwen3.5 會用長上下文處理複雜任務，建議至少保留 128K 上下文，以維持思考能力。」
- **建議取樣參數**（模型卡原文整理）：

  | 模式 | temperature | top_p | presence_penalty |
  |---|---|---|---|
  | 思考、一般任務 | 1.0 | 0.95 | 1.5 |
  | 思考、精確寫程式 | 0.6 | 0.95 | 0.0 |
  | 不思考、一般任務 | 0.7 | 0.8 | 1.5 |
  | 不思考、推理任務 | 1.0 | 0.95 | 1.5 |

  （top_k 都是 20，min_p 0。）Ollama 的 qwen3.5:9b 預設採用第一列。
- **Agent 用法**：建議用 [Qwen-Agent](../repos/QwenLM-Qwen-Agent.md)（可接 MCP）；Qwen Code 是「為 Qwen 模型最佳化」的終端機 agent。部署框架（vLLM、SGLang）的工具解析器指定 `qwen3_coder`，表示工具呼叫用的是 Qwen3-Coder 的 XML 格式（推論自參數名稱）。

## 證據

官方自測（`self_reported: true`），9B 這一欄：

| 類別 | 指標 | Qwen3.5-9B | 對照 |
|---|---|---|---|
| 一般 agent | BFCL-V4 | 66.1 | Qwen3-30B-A3B-Thinking-2507：42.4；Qwen3.5-4B：50.3 |
| 一般 agent | TAU2-Bench | 79.1 | Qwen3.5-4B：79.9 |
| 一般 agent | VITA-Bench | 29.8 | — |
| 一般 agent | DeepPlanning | 18.0 | — |
| 指令遵循 | IFEval | 91.5 | GPT-OSS-120B：88.9 |
| 指令遵循 | IFBench | 64.5 | GPT-OSS-120B：69.0 |
| 長上下文 | LongBench v2 | 55.2 | GPT-OSS-120B：48.2 |

- TAU2-Bench 的航空領域套用了 Claude Opus 4.5 系統卡提出的修正，其他照官方設定。
- 這些是用官方推論設定（通常是長上下文、思考模式）測的，不是 Ollama 量化版。

## 對 AI TA：可以借用／不適用

- **可以借用**：
  - 9B 在工具呼叫基準上明顯優於上一代 30B MoE（自測），支持「9B 能做 agent」的前提，但只到「單一領域、工具不多」的程度（推論：DeepPlanning 只有 18.0，長程規劃仍弱）。
  - 取樣參數依步驟切換：工具呼叫、批改用「不思考」或低溫；解釋用思考模式（推論）。
- **不適用／要注意**：
  - 「至少 128K 上下文」和本機預設 32k 衝突；實際影響要在 AI TA 的題組上測（推論：複習流程每次只需要少量講義段落，未必需要長上下文）。
  - 基準分數是官方設定下的成績，Ollama 的 nvfp4 量化版、不同 renderer 都可能讓實際表現不同；本機實驗看到的穩定度比這些分數暗示的差（見 [本機實驗](../internal/2026-local-qwen35-tool-calling.md)）。

## 限制與疑點

- 全是廠商自測，沒有獨立驗證。BFCL 官方排行榜（`gorilla.cs.berkeley.edu/data_overall.csv`，頁面標示 2026-04-12 更新）沒有任何 Qwen3.5 模型；最接近的是上一代 Qwen3-8B（FC 模式總分 42.57%），細項見 [BFCL 筆記](../papers/2025-bfcl.md)。
- 4B 的 TAU2-Bench（79.9）比 9B（79.1）還高，表示這類基準對模型大小不敏感，或測量誤差不小（推論）。
