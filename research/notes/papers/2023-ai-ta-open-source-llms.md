---
title: "AI-TA: Towards an Intelligent Question-Answer Teaching Assistant using Open-Source LLMs"
type: paper
tier: B
fit: 高
topics: [T1, T2, T6, T8]
year: 2023
venue: "NeurIPS 2023 Workshop on Generative AI for Education（GAIED）；arXiv 2311.02775 v3；Cornell、Microsoft Research、CMU、University of Auckland"
url: https://arxiv.org/abs/2311.02775
self_reported: true
status: read
accessed: 2026-11-11
---
## 一句話

用開源的 LLaMA-2（7B、13B、70B）做課程問答助教，比較 RAG、微調和偏好訓練：**RAG 的效果最大，只做微調反而變差**；13B 加上全部方法，人工評分接近、但仍低於 GPT-4 加 RAG。

## 他們怎麼做（架構、模型、資料）

- **動機**：用自家機器跑開源模型，學生資料不外流。
- **資料**：
  - 紐西蘭一所大學程式入門課（Matlab 和 C）8 個學期的 Piazza 討論區問答，去重後 10,647 筆。附圖的貼文全部排除。
  - 從 2022 學期留 717 筆評估，因為算力和預算只抽 236 筆。
  - 從貼文的編輯紀錄做出 1,549 組「修改前 vs 修改後」的偏好資料。
- **三種方法**：
  - **SFT**（supervised fine-tuning，監督式微調：拿問答對直接訓練模型）：LLaMA-2-13B-chat，用 QLoRA 4-bit，單張 A100、3 個 epoch。
  - **DPO**（Direct Preference Optimization：用「兩個回答哪個比較好」的成對資料訓練，比 RLHF 簡單、省資源）：單張 A6000。
  - **RAG**：
    - 用 Nougat（把 PDF 轉成 Markdown、能保留 LaTeX 公式的模型）處理課本和實驗手冊。
    - 每塊最多 1,000 字元、重疊 100 字元。
    - **混合檢索**：語意檢索 DPR 取前 3 段，加上 **BM25**（傳統的關鍵字比對搜尋）取前 2 段。作者觀察：語意檢索適合描述型問題，關鍵字檢索適合問特定函式名稱或作業題號的問題。
- **評估**：兩個指標「有用性」和「正確性」，各給 0、0.5 或 1 分。
  - 人工：20 題 × 9 個模型 = 180 個回答，只由 1 位作者評分。
  - 模型評審：GPT-4 評 236 題。

## 證據（怎麼評估、數字、樣本多大）

人工評分（兩個指標的平均，滿分 1）：

| 設定 | 分數 |
|---|---|
| LLaMA-2-13B | 0.24 |
| 13B + RAG | 0.51 |
| 13B + SFT | 0.11（變差，常編造） |
| 13B + SFT + DPO | 0.28 |
| 13B + SFT + DPO + RAG | 0.54 |
| LLaMA-2-70B | 0.26 |
| GPT-4 | 0.34 |
| GPT-4 + RAG | 0.69 |

- 摘要說的「改善 30%」其實是 0.24 → 0.54 的 +0.30 分（絕對差距），不是相對成長 30%。
- GPT-4 評審和人工評分的相關係數只有 0.66（Pearson），而且 GPT-4 評審把沒有 RAG 的 GPT-4 排第二，和人工結果不同。作者引用文獻認為 GPT-4 偏好 GPT 系列風格的回答。

## 對 AI TA：可以借用／不適用（原因）

- **可以借用**：
  - **先做 RAG，微調之後再說**。只用問答對微調，模型會更愛猜（T6）。
  - **混合檢索**（語意 + 關鍵字）。課程筆記裡常有英文術語和公式符號，關鍵字檢索可能補上語意檢索的漏洞（推論，T2 驗證）。
  - **轉換講義時保留 LaTeX**。公式不能在前處理就丟掉（T2）。
  - **模型評審只和人工中度相關**，評估不能只靠模型評分（T8）。
- **不適用**：
  - LLaMA-2 已經過時，數字不能直接套到 qwen3.5:9b。
  - 資料是討論區的歷年問答，AI TA 沒有這種資料可以微調。

## 限制與疑點

- 人工評估只有 20 題、1 位評分者，作者也承認樣本太小。
- 只有單一課程，沒有部署，也沒有使用者研究。
- 是 workshop 論文，審查比正式會議輕，所以列 B。
- 程式碼與部分資料：[aita-ai4ed/AITA](https://github.com/aita-ai4ed/AITA)（論文註腳提供）。2026-11-11 查：★1、最後更新 2025-04、沒有授權檔，不算持續維護的專案。
