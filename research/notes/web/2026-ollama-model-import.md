---
title: "Ollama 官方文件：匯入模型、Modelfile、ollama create 量化"
type: doc
tier: A
fit: 中
topics: [T6]
year: 2026
venue: "docs.ollama.com（2026-11-11 讀取）；本機 Ollama 0.40.10 的 `ollama create --help`"
url: https://docs.ollama.com/import
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

微調後的模型要回到 Ollama，目前官方文件只寫兩條路：匯入完整的 Safetensors 權重，或匯入 GGUF。舊版文件的 `ADAPTER`（直接掛 LoRA）已經不在 Modelfile 參考裡；本機 0.40.10 的 `ollama create` 可以把 Safetensors 量化成 nvfp4，並會做「MLX 驗證」。

## 他們怎麼做（架構、模型、資料）

- **[Importing a Model](https://docs.ollama.com/import)**：
  - Safetensors：Modelfile 寫 `FROM /權重資料夾`，再 `ollama create my-model`。
  - GGUF：`FROM /path/to/file.gguf`。Ollama 匯入時不會幫 GGUF 量化，要先用 llama.cpp 的 `llama-quantize` 做好。
- **[Modelfile 參考](https://docs.ollama.com/modelfile)**：
  - 指令有 FROM、PARAMETER、TEMPLATE、SYSTEM、LICENSE、MESSAGE、CAPABILITY、REQUIRES。**沒有 ADAPTER**（全文搜尋 `adapter`、`lora` 都沒有結果）。
  - Safetensors 的說明是「資料夾要包含受支援架構的權重」，但沒有列出支援哪些架構。
- **本機 `ollama create --help`（0.40.10）**：
  - `-q, --quantize`：把 Safetensors 模型量化到指定等級，例如 `nvfp4`。
  - `--force`：MLX 驗證失敗時仍繼續建立。
  - `--draft-quantize`：量化草稿模型（推測解碼用）。
- **本機 `/api/ps`**：已安裝的 qwen3.5:9b 是 safetensors 格式，由 `mlx` 執行器載入；`ollama show` 顯示量化為 `nvfp4`。

## 證據（怎麼評估、數字、樣本多大）

- 文件只說明流程，沒有數字。
- 「ADAPTER 已移除」是比對目前的 Modelfile 參考得出的。舊版文件內容是我的記憶，這次沒有找到舊版頁面佐證，所以只當背景，不當證據。

## 對 AI TA：可以借用／不適用（原因）

- **微調後的部署路線**（推論，全部待驗證）：
  1. mlx-lm 訓練 LoRA。
  2. `mlx_lm.fuse` 併回完整模型。
  3. 用 Ollama 的 Safetensors 匯入，加 `-q nvfp4` 量化。
  4. 用 Modelfile 設定系統提示和參數。

  第 3 步能不能接受 mlx-lm 融合出來的 Qwen3.5（多模態、混合注意力）是最大的不確定點。`--force` 的存在表示「MLX 驗證」可能失敗。
- **退路**：
  - 不微調，只用提示詞和 RAG（T6 統整的建議也是先這樣做）。
  - 或執行時直接用 mlx-lm 載入「底模＋LoRA」，不經過 Ollama。但這樣 AI TA 要同時管 Ollama 和 mlx-lm 兩套執行環境，記憶體裡也可能同時有兩份 9B（推論）。
- **Modelfile 本身就是不微調的個人化工具**：SYSTEM、MESSAGE（預先放幾輪示範對話）、PARAMETER（溫度、上下文長度）都可以固定下來，成本低、可以隨時改（推論）。

## 限制與疑點

- 沒有實際做匯入（依任務規定，不下載模型、不安裝 mlx-lm）。
- 文件沒有版本號；內容以 2026-11-11 讀到的為準。
