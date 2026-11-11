# eval

評估題組與每次的結果。

## 題組

| 檔案 | 內容 | 公開 |
|---|---|---|
| `midterm-baseline.jsonl` | 期中準備時在 Ollama App 問 qwen3.5:9b 的 16 個課程問題，附參考答案、答案所在的筆記段落、基準回答的量測。原始對話在 `records/ai-ta-build/2026-10-25_ollama-app_midterm-study.md`（只在本機） | 是 |
| `private/baseline-answers.jsonl` | 上面 16 題的基準回答全文，給評估時的「固定前文」和盲評用 | 否 |
| `runs/` | 每次評估的結果：設定、程式版本（Git commit）、逐題紀錄 | 是 |

從講義或練習題直接摘錄的題目不放公開的檔案，放 `private/`。

## 欄位（`midterm-baseline.jsonl`，一行一題）

| 欄位 | 意思 |
|---|---|
| `id` | `mb-<輪次>`，輪次對應原始紀錄的「第 N 輪」 |
| `session` | 哪一段讀書時間：`2026-10-25` 或 `2026-11-02` |
| `type` | 題型：`concept` 概念、`comparison` 比較、`check-understanding` 確認理解、`follow-up` 追問、`calculation` 計算、`formula` 公式解讀、`fact` 事實 |
| `follow_up_of` | 追問時，它接在哪一題後面；要連同前一題一起測 |
| `question_as_asked` | 當時送給模型的原文 |
| `question_restored` | 補回公式後的版本；只有 `formula_lost` 為 true 的題目才有 |
| `formula_lost` | 從 Obsidian 閱讀畫面複製時，數學式遺失了 |
| `pasted_from` | 問題文字的出處筆記與行號（路徑相對於 `Machine Learning/`） |
| `gold_sections` | 答案所在的筆記段落，用索引裡的段落 ID 表示；檢索評估用它算命中率 |
| `reference_points` | 參考答案，寫成 3–5 個要點，都出自筆記；標「補充（筆記沒寫）」的是筆記以外的正確內容，答出來加分、沒答不扣分 |
| `misconceptions` | 只有確認理解題才有：使用者說法裡每一點的判定（正確、需要修正、錯誤） |
| `grading_label` | 只有確認理解題才有：使用者說法整體的批改類別 |
| `reference_status` | `draft`：Claude 從筆記起草，還沒核對；`verified`：已由我核對 |
| `baseline` | 基準回答的量測：字數、從發問到答完的秒數、思考秒數、是否正確 |
| `user_rating` | 我對基準回答的評價，之後補 |

## 怎麼跑

```bash
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta eval-retrieval
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta eval-explain
```
