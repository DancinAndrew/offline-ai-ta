# Offline AI TA

一個能離線使用的 AI 助教，用來做機器學習課的考試型複習。它在筆電上跑本地的 9B 模型（透過 [Ollama](https://ollama.com) 執行 Qwen3.5-9B），根據我自己的課程筆記回答並附上出處，會出題、批改，並記住我哪裡常錯。

[English](README.md)

> **狀態：** 第一版可以用了，有終端機指令，也有只在本機開的複習網頁（Gradio）。搜尋、解釋、練習三種模式都跑在本機模型上，第一次評估的結果在 [`dev/eval/runs/`](dev/eval/runs/)。用法見 [`dev/README.md`](dev/README.md)，專案概覽見[提案](reports/2026-11-11-proposal.zh-TW.md)。

## 為什麼做

- **沒有網路也能用**：期中考前我在飛機上用過裸的本地模型。答案看得懂，但不夠好，而且當時什麼都沒調整。這個專案就從那次經驗出發。
- **個人化**：它根據我自己的講義筆記和作答紀錄回答，不是一般的聊天機器人。
- **課程要求**：這是中央大學機器學習課（2026 秋）的專題，學生要用本地模型做自己的 AI 助教。

## 核心假設

在有範圍、有講義的複習任務上，9B 本地模型加上設計良好的 harness（提示詞、工具、記憶、流程），可以接近 frontier 模型的品質。

驗證方式是用同一組題目跑三種設定：

1. 裸的本地模型（基準線）。
2. AI TA：同一個模型，加上這個專案的 harness。
3. Frontier 模型，給它同樣的講義（當上限參考，只在評估時使用）。

結果：我在 30 題保留題上做了這個比較。依我的盲評，AI TA 達到我在 2026-11-11（看到任何結果之前）訂下的三項標準：至少 75% 的題目被評為不輸 frontier 模型、答題時間中位數不超過 40 秒、答案長度中位數不超過 600 字（[標準](reports/2026-11-11-proposal.zh-TW.md)）。題數與評分者都很少，請當作一門課、一位學習者的證據來讀（見「限制」）。

## 做法

1. **研究**別人怎麼做課程 AI 助教、怎麼讓回答根據講義、怎麼用小模型做 agent、怎麼評估助教。→ [`research/`](research/)
2. **決定**設計，依據研究結果。→ [`docs/decisions/`](docs/decisions/)
3. **建置**：先做最小可用的離線版，再做 agent 和介面。→ `dev/`
4. **評估與報告**。→ `reports/`

步驟順序與決策紀錄見 [`docs/plan.md`](docs/plan.md)。

## 快速開始

需要 [Ollama](https://ollama.com)、Python 3.12 以上，以及你自己的課程筆記（這個 repo 不含任何課程檔案）。

```bash
ollama pull qwen3.5:9b && ollama pull qwen3-embedding:0.6b
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

筆記是原地讀取的：把這個資料夾放進你的筆記資料夾，再改 [`data/knowledge/sources.json`](data/knowledge/sources.json) 裡的路徑樣式。然後建索引、開始一段複習；各指令見 [`dev/README.md`](dev/README.md)。

```bash
PYTHONPATH=dev/src .venv/bin/python -m ai_ta index
PYTHONPATH=dev/src .venv/bin/python -m ai_ta embed
PYTHONPATH=dev/src .venv/bin/python -m ai_ta web --open
```

## 限制

- **小樣本、單一評分者**：保留題只有 30 題，評分者只有我，所以不確定範圍很寬。例如 30 題中 23 題通過，95% 信賴區間約 59% 到 88%（見 [決策 0006](docs/decisions/0006-eval-set-split.md)）。
- **開發題的批改結果是暫定的**：開發題的正確／部分正確／錯誤數量來自 AI 審查（Claude），不是我批改的；盲評比較是唯一由我自己判斷的結果。
- **一門課、一位學習者**：它是針對我自己的中文筆記和一門機器學習課調整的，沒有在其他科目或其他學生身上試過。
- **受筆記限制**：筆記沒寫到的地方，助教設計成直接說明沒有，而不是憑記憶補答案。

## 資料夾

| 資料夾 | 內容 |
|---|---|
| `research/` | 依證據強度分 A／B／C 的來源筆記、搜尋紀錄、統整（繁體中文） |
| `docs/` | 規劃、課程要求、設計決策（繁體中文） |
| `dev/` | 程式、harness（提示詞與工具說明）、介面、評估 |
| `data/` | 執行時資料的清單；課程檔案不重新散布 |
| `reports/` | 給專案外讀者的報告（英文與繁體中文） |

不公開：AI 互動紀錄、個人學習資料、論文 PDF、課程講義。

## 授權

[MIT](LICENSE)
