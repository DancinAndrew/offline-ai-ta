---
title: "Small LLMs Are Weak Tool Learners: A Multi-LLM Agent（α-UMi）"
type: paper
tier: A
fit: 中
topics: [T5, T4]
year: 2024
venue: "EMNLP 2024 Main（2024.emnlp-main.929，pp. 16658–16680）；中山大學＋阿里巴巴；程式 X-PLUG/Multi-LLM-Agent"
url: https://aclanthology.org/2024.emnlp-main.929/
self_reported: true
status: read
accessed: 2026-11-11
---
## 一句話

一個小模型同時負責「規劃、呼叫工具、寫最終回答」會顧此失彼；把三件事拆給三個各自微調的小模型（planner、caller、summarizer），7B 就能在 ToolBench 上贏過單一 13B，部分指標接近 GPT-4。

## 他們怎麼做

- **拆角色**：
  - Planner：看目前軌跡，寫下這一步的理由，並決定下一步是「叫 caller」「叫 summarizer」或「放棄」。
  - Caller：依 planner 的理由產生合法的工具呼叫。
  - Summarizer：根據整個軌跡寫給使用者的最終答案。
  - 三者各有自己的系統提示和輸入，輪流執行直到 planner 決定結束。
- **兩階段微調（GLPFT）**：先用完整資料微調一個骨幹模型（讓它理解整個任務），再複製成三份，各自用重新整理過的子任務資料繼續微調。
- **模型與資料**：LLaMA-2-chat-7B／13B；ToolBench（RapidAPI 的真實 API）。

## 證據（作者自測）

- **ToolBench 同分布測試**（Table 1，7B）：

  | 方法 | 規劃正確率 | 動作完全正確 | 幻覺率 | 參數 F1 |
  |---|---|---|---|---|
  | 單一 LLM（7B 微調） | 81.92 | 53.26 | 2.32 | 45.57 |
  | α-UMi（7B，三個模型） | 88.92 | 58.94 | 0.57 | 52.24 |
  | GPT-4（零樣本） | 80.28 | 55.52 | 5.98 | 48.74 |

- 7B 的 α-UMi 勝過 13B 的單一模型。
- 直接各自微調三個模型（不做第一階段）反而比單一模型差；用 LoRA 取代全參數微調也較差。作者結論：全參數微調是必要的。
- 真實 API 測試（Table 2）：7B α-UMi 的通過率勝過 GPT-3.5 和 ToolLLaMA，但 win rate 仍低於 GPT-4。

## 對 AI TA：可以借用／不適用

- **可以借用**：
  - **一次只讓模型做一種事**：AI TA 的每一步（決定下一題、呼叫檢索、寫解釋、批改）用不同的短提示、只給該步需要的工具，即使底下是同一個 qwen3.5:9b（推論：論文用的是三個不同權重的模型，「同一個模型換提示」沒被測過）。
  - Planner 有「放棄」選項：AI TA 遇到講義查不到時，應該明確說不知道，而不是硬答。
- **不適用**：
  - 需要全參數微調三份模型；9B 的三份權重在 32 GB Mac 上無法同時載入，也不可能在本機全參數微調（推論；Mac 微調的可行性見 [mlx-lm 筆記](../repos/ml-explore-mlx-lm.md)、[QLoRA 筆記](2023-qlora.md)）。
  - LLaMA-2 是沒有原生工具呼叫的舊模型；qwen3.5:9b 單一模型的工具呼叫能力可能已超過論文的單一 7B 基線（推論）。

## 限制與疑點

- 數字都是作者自測；ToolBench 的評估部分依賴 GPT 評審（真實 API 測試的 win rate）。
- 標題的「小模型是弱的工具學習者」指的是 2023 年的 LLaMA-2 世代；對 2026 年原生訓練工具呼叫的 9B 是否仍成立，要靠 [BFCL](2025-bfcl.md) 這類較新的數字判斷（單輪已接近頂尖，多輪仍弱）。
- PDF 存在 `research/pdfs/2024-small-llms-weak-tool-learners.pdf`。
