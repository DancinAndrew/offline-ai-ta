# 0001 基礎模型用官方 qwen3.5:9b

- 日期：2026-11-09
- 狀態：已採用

## 背景

AI TA 必須跑本地模型（課綱要求），機器是 Apple M5、32 GB，用 Ollama（0.40.10）。當時本機有三個模型：

- qwen3.6:35b-a3b-coding（23 GB）
- qwen3-coder:30b（18 GB）
- qwen3.5:9b（7.6 GB）

另外考慮過網路上流傳的「蒸餾 DeepSeek、跑分很高」的 Qwen3.5 9B 版本。

## 選項

1. **官方 qwen3.5:9b**：9.7B 參數、nvfp4 量化、7.6 GB，支援看圖、工具呼叫、思考模式，Apache-2.0 授權。
2. **Jackrong 的 DeepSeek-V4 蒸餾版**（社群微調，不是 Qwen 或 DeepSeek 官方發布）：
   - Ollama 上能下載的是 Flash 版，由第三方重新打包，例如 `pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2`（6.6 GB）。它只用約 8,000 筆資料訓練，頁面上沒有跑分。
   - 宣稱跑分 90.53% 的是 Pro 版，Ollama 上沒有。這個數字只測了 MMLU-Pro 的數學、物理、化學三科，各抽 500 題。同一位作者測官方版得到 89.60%，只差 0.93 分；1,500 題的抽樣誤差約 ±1 分，這個差距在誤差範圍內。

## 決定

用官方 qwen3.5:9b。兩個寫程式用的模型刪掉，空出 41 GB。

## 理由

- 蒸餾版的優勢沒有被證明：唯一的數字是作者自己測的，只測三科，而且差距在誤差範圍內。
- 官方模型來源清楚、容易重現，報告裡好交代；看圖能力也有官方支援。
- 個人化靠的是 RAG 和 harness，不是換一個在數學題上多 1 分的模型。

## 後果

- 2026-11-09 實測：繁體中文回答正確，第一次載入約 7 秒，生成速度約每秒 13.4 個 token。
- 如果評估發現模型本身是瓶頸，再拿其他模型（包括蒸餾版）在自己的評估題組上比較。

## 來源

- [Jackrong/DeepSeek-V4-Pro-Qwen3.5-9B](https://huggingface.co/Jackrong/DeepSeek-V4-Pro-Qwen3.5-9B)：Pro 版模型卡與跑分表
- [Jackrong/Qwen3.5-9B-DeepSeek-V4-Flash-GGUF](https://huggingface.co/Jackrong/Qwen3.5-9B-DeepSeek-V4-Flash-GGUF)：Flash 版模型卡
- [pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2](https://ollama.com/pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2)：Ollama 上的第三方重新打包版
- [qwen3.5:9b](https://ollama.com/library/qwen3.5:9b)：Ollama 官方模型頁
