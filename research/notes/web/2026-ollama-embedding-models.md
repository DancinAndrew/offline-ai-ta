---
title: "Ollama 官方模型庫與文件：嵌入模型、/api/embed、判斷模型（decision）"
type: doc
tier: A
fit: 高
topics: [T2]
year: 2026
venue: "Ollama 官方網站與文件（本機 Ollama 0.40.10；頁面於 2026-11-11 讀取）"
url: https://ollama.com/search?c=embedding
self_reported: true
status: read
accessed: 2026-11-11
---
## 一句話

Ollama 官方模型庫目前有十幾個可離線跑的嵌入模型，其中標明支援多語（含中文）的主要是 bge-m3、qwen3-embedding、embeddinggemma（1 與 2 代）、nomic-embed-text-v2-moe、snowflake-arctic-embed2。Ollama 沒有重排序（rerank）端點，但 2026 年多了「判斷模型」（decision），可以回傳是／否的機率，或許能拿來代替重排序和出處檢查，要實測。

## 他們怎麼做（架構、模型、資料）

**嵌入模型**（embedding model：把一段文字轉成一串數字，意思相近的文字數字也相近，用來找相關段落）。以下整理自 [嵌入模型列表](https://ollama.com/search?c=embedding) 和各模型的官方頁面。語言支援照頁面原文，沒寫的就標「頁面未說明」。

| 模型（Ollama 名稱） | 大小 | 上下文 | 語言（頁面原文） | 備註 |
|---|---|---|---|---|
| `bge-m3`（567m） | 1.2 GB | 8K | 100 多種 working languages | XLM-RoBERTa；論文見 [BGE-M3 筆記](../papers/2024-bge-m3.md)；頁面兩年未更新 |
| `qwen3-embedding`（0.6b／4b／8b） | 639 MB／2.5 GB／4.7 GB | 32K／40K／40K | 100+ languages | 8B 在 MTEB 多語排行榜第 1（2025-06-05，70.58，廠商宣稱）；可自訂輸出維度、可加任務指令 |
| `embeddinggemma`（300m） | 622 MB | 2K | 用 100+ 種語言的資料訓練 | 需要 Ollama 0.11.10 以上 |
| `embeddinggemma-2`（270m 文字版、440m／570m／740m 多模態） | 304 MB 起 | 頁面列 256K，說明文字寫 8,192 tokens | 100+ languages | 3 週前上架；MTEB 多語 v2 61.36（廠商宣稱）；向量可截短到 128／256／512 維 |
| `nomic-embed-text-v2-moe` | 958 MB | **512** | 約 100 種語言 | 查詢和文件要加不同前綴（`search_query:`、`search_document:`） |
| `snowflake-arctic-embed2`（568m） | 1.2 GB | 8K | 多語（頁面舉英、法、西、義、德的評估） | 頁面未列中文 |
| `granite-embedding:278m` | 563 MB | 512 | 12 種，含 Chinese (Simplified) | 30m 版只有英文 |
| `paraphrase-multilingual`（278m） | 563 MB | 512 | 頁面未列語言清單 | Sentence-BERT 系列，較舊 |
| `nomic-embed-text`、`mxbai-embed-large`、`all-minilm`、`snowflake-arctic-embed`、`bge-large` | — | — | 頁面未說明多語，或以英文為主 | 不列入候選 |

**API**（[/api/embed](https://docs.ollama.com/api/embed)、[Embeddings 說明](https://docs.ollama.com/capabilities/embeddings)）：

- `input` 可以一次送一串文字，回傳一組向量；向量已正規化成長度 1，所以用 cosine 相似度即可。
- `truncate` 預設是 `true`：**超過模型上下文的輸入會被默默截掉**，設成 `false` 才會報錯。
- `dimensions`：指定輸出維度（給支援截短的模型用）。
- 官方提醒：建索引和查詢要用同一個嵌入模型。
- 每段輸入只回傳一個向量。

**重排序**（reranking：先粗撈 20–150 段，再用比較準但比較慢的模型重新排序）：

- [docs.ollama.com 的文件總表](https://docs.ollama.com/llms.txt) 沒有 rerank 頁面，API 也沒有 rerank 端點（2026-11-11 查）。
- 新的 **判斷模型**（[Decision 說明](https://docs.ollama.com/capabilities/decision)，`/v1/systemone` 端點）：給一段文字（state）和最多 64 個問題，回傳「是／否」機率、選項機率或評分等級。官方例子是工單分類，不是檢索。
  - `nimble`：9B，從 Qwen3.5-9B 微調，9.3 GB。
  - `tev1`：0.8B／4B，從 Qwen3.5 微調。
  - `laya`：421M，從 ModernBERT-large 微調，有 322m 多語版本；廠商說訓練任務含「fact verification」（事實查核）。
  - 速度都是廠商自測，例如 laya 在 M5 Max 上單題 10 毫秒以內、nimble 100 毫秒以內。

## 證據（怎麼評估、數字、樣本多大）

- 表裡的跑分都是廠商自己公布的（`self_reported: true`），而且是通用基準，沒有繁體中文或課程講義的數字。
- **本機實測（2026-11-11，Ollama 0.40.10）**：
  - 對 `qwen3.5:9b` 呼叫 `/api/embed`，回傳錯誤 `input after truncation exceeds maximum context length`（輸入只有幾個字）。也就是說，生成模型不能兼當嵌入模型，一定要另外下載嵌入模型。
  - `/api/ps` 顯示 qwen3.5:9b 是 safetensors 格式、由 `mlx` 執行器載入、預設上下文 32,768、佔 7.6 GB。

## 對 AI TA：可以借用／不適用（原因）

- **候選嵌入模型**（要在自己的題組上比，不能只看排行榜）：
  - `bge-m3`：有論文、有繁中跨語言數字，1.2 GB。
  - `qwen3-embedding:0.6b`：和生成模型同一家族，639 MB，可以加任務指令。
  - `embeddinggemma-2:270m`：最新、最小。
- **記憶體預算**（推論）：qwen3.5:9b 佔 7.6 GB，加一個 0.6–1.2 GB 的嵌入模型，32 GB 的機器放得下。要再加 9B 的判斷模型就偏緊，應優先考慮 laya 或 tev1:0.8b 這類小模型。
- **切段長度要配合模型上下文**：nomic v2 和 granite 只有 512 token，而且 API 預設會默默截斷。筆記一個問題小節常有上千字，要嘛選 8K 以上的模型，要嘛切段時檢查長度（推論）。
- **重排序和出處檢查**：判斷模型可以問「這段講義能不能回答這個問題？」或「這段講義能不能推出這句話？」，再用機率排序或篩選。這可以補 ALCE 的出處檢查（見 [ALCE 筆記](../papers/2023-alce.md)），但官方沒有拿它做檢索的評估，**完全是推論，要實測**。
- **混合檢索的關鍵字那一路**：Ollama 只給一個向量，BGE-M3 的 sparse 分數拿不到，關鍵字檢索得另外做。

## 限制與疑點

- 頁面內容會變，模型清單和數字是 2026-11-11 的版本。
- embeddinggemma-2 的上下文，頁面表格寫 256K，說明文字寫 8,192 tokens，兩者不一致；以實測為準。
- 判斷模型的語言支援，nimble 和 tev1 頁面沒寫（底座 Qwen3.5 支援中文，但微調資料未說明）；只有 laya 有標 multilingual 版本。
- 依任務規定，這次沒有下載任何模型，所以嵌入模型的中文效果和速度都還沒在本機驗證。
