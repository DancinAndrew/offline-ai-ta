# eval

評估題組與每次的結果。題組的來源和切分方式見決策紀錄 [0006](../../docs/decisions/0006-eval-set-split.md)。

## 題組

| 檔案 | 題數 | 內容 | 公開 |
|---|---:|---|---|
| `midterm-baseline.jsonl` | 16 | 期中準備時在 Ollama App 問 qwen3.5:9b 的課程問題，附參考答案、答案所在的筆記段落、基準回答的量測。原始對話在 `records/ai-ta-build/2026-10-25_ollama-app_midterm-study.md`（只在本機） | 是 |
| `self-check.jsonl` | 28 | 週筆記「自我檢查」的題目，參考答案是筆記裡的答案 | 是 |
| `traps.jsonl` | 10 | 陷阱題：一個對的說法加一個改錯的說法，用「……對嗎？」問 | 是 |
| `private/practice.jsonl` | 10 | `Midterm Review/08_練習題` 的歷屆原題，參考要點從詳解整理 | 否 |
| `private/baseline-answers.jsonl` | — | `midterm-baseline` 的基準回答全文，給評估時的「固定前文」和盲評用 | 否 |
| `runs/` | — | 每次評估的結果：設定、程式版本（Git commit）、逐題紀錄 | 是 |
| `private/runs/` | — | 私有題組（練習題）的逐題紀錄。回答會帶出原題，所以和公開紀錄分開存；公開紀錄的 `kept_private` 列出移到這裡的題號 | 否 |

從講義或練習題直接摘錄的題目不放公開的檔案，放 `private/`。

## 開發／測試切分

- `midterm-baseline` 全部是 dev，因為第 5 步已經用它調整過。其他三組依檔案順序，第 0、3、6……題是 dev，其餘是 test。
- 合計 dev 34 題、test 30 題。
- 開發時只跑 dev。test 留到第 7 步跑一次：程式預設只載入 dev，要跑 test 必須加 `--allow-test`。

## 欄位（一行一題）

| 欄位 | 意思 |
|---|---|
| `id` | `mb-<輪次>`（對應原始紀錄的「第 N 輪」）、`sc-<自我檢查題依週次的編號>`、`tr-<編號>`、`pr-<原題號>` |
| `set` | 屬於哪個題組 |
| `split` | `dev` 或 `test` |
| `type` | 題型：`concept` 概念、`comparison` 比較、`check-understanding` 確認理解、`follow-up` 追問、`calculation` 計算、`formula` 公式解讀、`fact` 事實 |
| `topic` | 主題 |
| `follow_up_of` | 追問時，它接在哪一題後面；要連同前一題一起測 |
| `question_as_asked` | 送給模型的原文 |
| `question_restored` | 補回公式後的版本；只有 `formula_lost` 為 true 的題目才有 |
| `gold_sections` | 答案所在的筆記段落，用索引裡的段落 ID 表示；檢索評估用它算命中率。可能標不完整，漏題要先確認是不是標漏（0006 有補標的規則） |
| `reference_points` | 參考答案的要點；標「補充（筆記沒寫）」的是筆記以外的正確內容，答出來加分、沒答不扣分 |
| `reference_answer` | 只有 self-check 有：筆記裡的答案原文。要點是程式拆句的，批改以原文為準 |
| `misconceptions` | 確認理解題和陷阱題才有：使用者說法裡每一點的判定（正確、需要修正、錯誤） |
| `grading_label` | 確認理解題和陷阱題才有：使用者說法整體的批改類別 |
| `reference_status` | `draft`：Claude 起草，還沒核對；`verified`：我核對過；`from-notes`：取自筆記的答案；`from-solutions`：Claude 從詳解整理 |
| `source` | self-check 和 practice 才有：題目出自哪份筆記或哪一題 |

只有 `midterm-baseline` 有的欄位：

| 欄位 | 意思 |
|---|---|
| `turn`、`session`、`asked_at` | 原始紀錄的第幾輪、哪一段讀書時間（`2026-10-25` 或 `2026-11-02`）、發問時間 |
| `formula_lost` | 從 Obsidian 閱讀畫面複製時，數學式遺失了 |
| `pasted_from` | 問題文字的出處筆記與行號（路徑相對於 `Machine Learning/`） |
| `baseline` | 基準回答的量測：字數、從發問到答完的秒數、思考秒數、是否正確 |
| `user_rating` | 我對基準回答的評價，之後補 |

## 怎麼跑

```bash
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta eval-retrieval
```

```bash
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta eval-explain --set traps --set self-check
```

- `--set`：只跑指定的題組，可以重複；預設全部。沒有 `private/practice.jsonl` 時自動略過。
- `--split`：`dev`（預設）、`test`、`all`；後兩個要加 `--allow-test`。
- 正確段落在索引裡找不到時（例如筆記標題改了），程式會列出是哪幾題並停下，先修題組再跑。
