---
title: "QLoRA: Efficient Finetuning of Quantized LLMs"
type: paper
tier: A
fit: 中
topics: [T6]
year: 2023
venue: "NeurIPS 2023 oral（OpenReview 論壇 OUIFPHEgJU；arXiv 2305.14314；University of Washington）"
url: https://arxiv.org/abs/2305.14314
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

先把模型壓成 4-bit 並凍結，只訓練外掛的小矩陣（LoRA），就能用一張 48 GB 的 GPU 微調 65B 模型，效果接近 16-bit 全參數微調。這是「在 32 GB 的 Mac 上微調 9B」可行性的理論依據。

## 他們怎麼做（架構、模型、資料）

- **LoRA**（low-rank adaptation，低秩適配）：原本的權重不動，在旁邊加兩個很瘦的矩陣 L₁（h×r）和 L₂（r×o），只訓練這兩個。r 很小，所以要訓練、要存的參數只有原模型的千分之幾。
- **QLoRA 的三個省記憶體技巧**：
  - **4-bit NormalFloat（NF4）**：針對常態分布的權重設計的 4-bit 格式，比一般 4-bit 整數或浮點更準。
  - **Double Quantization**：把量化用的縮放常數再量化一次，每個參數再省約 0.37 bit（65B 模型約省 3 GB）。
  - **Paged Optimizers**：用 NVIDIA 的 unified memory，在 GPU 記憶體不夠時把優化器狀態暫存到 CPU 記憶體。
- **計算方式**：權重用 4-bit 存，運算時解壓成 BFloat16；梯度只算 LoRA 參數的。

## 證據（怎麼評估、數字、樣本多大）

- **記憶體拆解**（第 2 節，7B LLaMA、batch size 1）：
  - 4-bit 底模型：5,048 MB。
  - LoRA 參數：26 MB。
  - 輸入梯度（activation gradients）：567 MB；開 gradient checkpointing（反向傳播時重算中間值、不全部存著）後，每個序列約 18 MB。
  - 作者結論：記憶體大頭是底模型和中間值，不是 LoRA 參數。
- **效果**：
  - 4-bit QLoRA 在 GLUE、Super-NaturalInstructions、MMLU 上追平 16-bit 全參數微調和 16-bit LoRA。
  - 前提是**每一層的所有線性層都加 LoRA**；只加在 attention 的 query／value（早期常見做法）追不上。
- **資料品質勝過數量**：9k 筆的 OASST1 比 45 萬筆的 FLAN v2 子集更能提升聊天表現。
- 規模：訓練超過 1,000 個模型，80M 到 65B。

## 對 AI TA：可以借用／不適用（原因）

- **記憶體估算**（推論，用論文的拆解套到 Qwen3.5-9B）：
  - Hugging Face 上 Qwen3.5-9B 的 BF16 權重約 96.5 億參數，約 19.3 GB。用 16-bit 做 LoRA，光權重就佔 32 GB 的六成，加上中間值很緊。
  - 4-bit 權重約 5–6 GB，加上 LoRA、優化器和中間值，在 32 GB 上有餘裕。
  - 結論：**在 32 GB 的 Mac 上做 9B 微調，實際可行的是 QLoRA（4-bit），不是 16-bit LoRA**。
- **不能直接套用：實作**。論文的實作（bitsandbytes、paged optimizers）是給 NVIDIA CUDA 的；Mac 上要用 Apple 的 MLX（見 [mlx-lm 筆記](../repos/ml-explore-mlx-lm.md)），它有自己的量化格式和 QLoRA 實作，記憶體數字要重測。
- **可以借用：設定原則**。LoRA 要加在所有線性層；資料品質比數量重要。後者對「只有幾百筆互動紀錄」的我們是好消息（推論）。

## 限制與疑點

- 實驗模型是 LLaMA、T5 等 2023 年的架構。Qwen3.5 是混合架構（32 層裡 24 層是線性注意力），4-bit 微調的品質和記憶體行為沒有人在這篇驗證過。
- 論文主要評估聊天和通用基準，不是「把課程知識教進模型」；後者見 [Fine-Tuning or Retrieval 筆記](2024-fine-tuning-or-retrieval.md) 和 [新知識筆記](2024-new-knowledge-hallucination.md)。
