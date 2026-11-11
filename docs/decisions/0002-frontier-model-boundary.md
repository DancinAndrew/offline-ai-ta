# 0002 frontier 模型的使用界線

- 日期：2026-11-11
- 狀態：已採用

## 背景

計畫原本只寫「frontier 模型只在評估時使用，AI TA 執行時不依賴它」。第 2 步研究提出兩個新用途：

- 開發期讓 frontier 模型讀失敗案例，提出 harness 的改良建議（[T4](../../research/synthesis/T4.md)）。
- 產生微調用的訓練資料（[T6](../../research/synthesis/T6.md)）。

另外，開發本身就是由 Claude Code 協助完成的，而 Claude 就是 frontier 模型。

## 決定

- **執行時**：一律離線，只用本機的 qwen3.5:9b 和嵌入模型。
- **開發與評估時可以用 frontier 模型**，用途包括：
  - 寫程式、提示詞和文件；
  - 起草評估題組的參考答案，由我核對後才定案；
  - 當輔助評審，最終分數仍以我的盲評為準（見 [0003](0003-evaluation-design.md)）；
  - 讀評估的失敗案例，提出 harness 改良建議；
  - 當三方比較的對照組（見 [0003](0003-evaluation-design.md)）。
- **暫不決定**：要不要用 frontier 模型產生微調訓練資料。等評估後真的要微調時再決定（見 [0004](0004-architecture.md)）。

## 規則

- **每次使用都要留紀錄**：
  - 程式和文件由 Git 歷史與 `records/` 的對話紀錄涵蓋。
  - 評估相關的使用（起草答案、評審、改良建議）記在 `dev/eval/` 的評估紀錄。
- **對外報告要寫清楚**：AI TA 執行時完全離線；開發與評估有 frontier 模型參與；哪些改良來自 frontier 的建議。

## 理由

- 課程和使用情境的硬性要求是「執行時離線」，開發期用 frontier 模型並不違反。
- 開發本來就由 Claude Code 協助，禁止反而做不下去，重點在於透明。
- 評估需要大量判斷，全部靠人工的話，題組沒辦法擴充（見 [0003](0003-evaluation-design.md)）。

## 後果

- 「AI TA 的提升有多少來自 frontier 的建議」必須能從紀錄追溯。
- 如果評估顯示 AI TA 接近 frontier，結論要附上這個限制：harness 是在 frontier 模型協助下設計的。
