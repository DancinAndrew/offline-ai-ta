---
title: "mlx-lm：在 Apple Silicon 上用 MLX 跑和微調 LLM（含 LORA.md）"
type: repo
tier: A
fit: 中
topics: [T6]
year: 2026
venue: "ml-explore/mlx-lm；GitHub ★ 7.6k；最後推送 2026-11-06；MIT；Apple ml-explore 官方"
url: https://github.com/ml-explore/mlx-lm
self_reported: true
status: read
accessed: 2026-11-11
---
## 一句話

Apple 官方的 MLX 套件 mlx-lm 可以在 Mac 上做 LoRA 和 QLoRA 微調，官方文件說 32 GB 的機器能微調 7B 模型。repo 裡已經有 Qwen3.5 的模型程式，但文件沒說它支援 LoRA，也不能把 Qwen3.5 匯出成 GGUF。

## 他們怎麼做（架構、模型、資料）

以下整理自 [LORA.md](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md)（最後修改 2026-09-24）和 [README](https://github.com/ml-explore/mlx-lm)：

- **指令**：`mlx_lm.lora --model <模型> --train --data <資料夾> --iters 600`。
  - 微調類型有 `lora`（預設）、`dora`、`full`。
  - `--model` 指向量化過的模型時，自動變成 QLoRA。
- **資料格式**：`train.jsonl`（必要）、`valid.jsonl`（選用，回報驗證損失）、`test.jsonl`。每行一筆，支援 `chat`（messages 陣列）、`tools`（含工具呼叫）、`completions`、`text` 四種。
  - `--mask-prompt`：只對回答部分算損失；chat 格式以最後一則訊息當回答。
- **融合與匯出**：
  - `mlx_lm.fuse` 把 LoRA 併回模型，存成 `fused_model/`。
  - `--export-gguf` 可以匯出 GGUF，但**只支援 Mistral、Mixtral、Llama 類模型的 fp16**。
- **LoRA 支援的模型家族**（文件原文）：Mistral、Llama、Phi2、Mixtral、Qwen2、Gemma、OLMo、MiniCPM、InternLM2。
- **repo 的模型程式**（`mlx_lm/models/`，2026-11-11 查）：有 `qwen3_5.py`（最後修改 2026-10-09）、`qwen3_5_moe.py`、`qwen3_next.py` 等。
- **省記憶體的方法**（文件「Memory Issues」）：
  - 用 QLoRA。
  - `--batch-size` 降到 1–2，搭配 `--grad-accumulation-steps` 累積梯度。
  - `--num-layers` 從預設 16 降到 8 或 4，只微調最後幾層。
  - 縮短每筆樣本。
  - `--grad-checkpoint`。
- **大模型提示**（README）：模型相對記憶體太大時會變慢，可以用 `sudo sysctl iogpu.wired_limit_mb=N` 提高可固定給 GPU 的記憶體上限，需要 macOS 15 以上。

## 證據（怎麼評估、數字、樣本多大）

- 官方唯一的數字（廠商自測）：32 GB 的 M1 Max，用 `--batch-size 1 --num-layers 4` 微調 Mistral-7B（WikiSQL 資料），約每秒 250 token。
- 沒有 Qwen3.5 或 9B 的微調數字，也沒有品質評估。

## 對 AI TA：可以借用／不適用（原因）

- **可行性**（推論）：32 GB 的 Mac 微調 9B，技術上應該可行（QLoRA＋batch 1＋少量層），但有三個未確認的環節：
  1. Qwen3.5 是混合架構（24 層線性注意力＋8 層全注意力），repo 有推論用的模型程式，但 LoRA 文件沒列，要實測能不能訓練。
  2. Ollama 上的 qwen3.5:9b 是多模態模型（Hugging Face 上是 `Qwen3_5ForConditionalGeneration`，image-text-to-text）。只微調文字部分要另外處理視覺權重。
  3. 微調完要回到 Ollama：GGUF 匯出不支援 Qwen；Ollama 0.40 可以直接匯入 Safetensors 並用 `-q nvfp4` 量化（見 [Ollama 匯入筆記](../web/2026-ollama-model-import.md)），但能不能吃 mlx-lm 融合後的 Qwen3.5 檔案，沒有驗證。
- **可以借用：資料格式**。chat 格式加 `--mask-prompt`，正好對應「問題＋檢索段落 → 附出處回答」的 RAFT 式資料（見 [RAFT 筆記](../papers/2024-raft.md)）。
- **可以借用：有驗證集就能提早停止**，避免 [新知識筆記](../papers/2024-new-knowledge-hallucination.md) 提到的過擬合。
- **不適用：官方的 7B 範例不等於 9B 可行**。量化格式、架構、上下文長度都不同（推論）。

## 限制與疑點

- 依任務規定沒有安裝 mlx-lm，以上全部是讀文件和原始碼目錄，沒有本機實測。
- LORA.md 的模型清單看起來沒有隨 repo 更新（repo 有 Qwen3、Gemma3 等程式，但清單只寫到 Qwen2、Gemma），所以「清單沒列」不等於「不支援」，反之亦然。
