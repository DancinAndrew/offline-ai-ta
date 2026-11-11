# eval

評估題組與結果。`dev/` 其他部分的結構等開發階段再定。

## 題組

| 檔案 | 內容 |
|---|---|
| `midterm-baseline.jsonl` | 期中準備時在 Ollama App 問 qwen3.5:9b 的 16 個課程問題，附基準回答的量測。原始對話在 `records/ai-ta-build/2026-10-25_ollama-app_midterm-study.md`（只在本機） |

從講義或練習題直接摘錄的題目不放這裡，因為這個資料夾會公開。

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
| `reference_answer` | 參考答案；目前只有可客觀判斷的 2 題，其他之後補 |
| `baseline` | 基準回答的量測：字數、從發問到答完的秒數、思考秒數、是否正確 |
| `user_rating` | 使用者對基準回答的評價，之後補 |
