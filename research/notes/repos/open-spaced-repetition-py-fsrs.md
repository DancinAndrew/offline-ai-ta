---
title: "py-fsrs：FSRS 間隔重複排程的 Python 實作（只看怎麼存使用者狀態）"
type: repo
tier: B
fit: 高
topics: [T6, T3]
year: 2026
venue: "open-spaced-repetition/py-fsrs；GitHub ★ 530；最後推送 2026-08-09；MIT（同組織的 fsrs4anki ★ 4.1k、MIT）"
url: https://github.com/open-spaced-repetition/py-fsrs
self_reported: true
status: read
accessed: 2026-11-11
---
## 一句話

FSRS（Free Spaced Repetition Scheduler，預測「什麼時候快忘了」來排下一次複習的演算法）把每張卡片的狀態壓成幾個數字，另外保留每次作答的紀錄；紀錄夠多時，可以用紀錄重新擬合參數。這種「事件紀錄＋可重算的狀態」設計，可以直接拿來存 AI TA 的使用者狀態。學習科學的部分（間隔效應為什麼有效）屬於 T3。

## 他們怎麼做（架構、模型、資料）

以下整理自 [README](https://github.com/open-spaced-repetition/py-fsrs) 和 [`fsrs/card.py`](https://github.com/open-spaced-repetition/py-fsrs/blob/main/fsrs/card.py)：

- **三個物件，都能存成 JSON**（`to_json`／`from_json`）：
  - `Card`（一張卡片的目前狀態）：
    - `card_id`、`state`（Learning 初學／Review 複習中／Relearning 忘了重學）、`step`（初學或重學的第幾步）。
    - **`stability`**（穩定度：記憶能撐多久）、**`difficulty`**（難度）。
    - `due`（下次該複習的時間）、`last_review`。
  - `ReviewLog`（每次作答一筆）：卡片、評分、作答時間。
  - `Scheduler`（排程器）：21 個模型權重、`desired_retention`（想維持的記得機率，預設 0.9）、初學和重學的間隔步數、最長間隔、是否加隨機擾動。
- **作答評分**：Again（忘了）／Hard／Good／Easy 四級。
- **可記得的機率（retrievability）**：可以隨時從卡片狀態算出「現在還記得的機率」，例如 0.94。
- **選用的最佳化器**：拿一批 `ReviewLog` 重新擬合 21 個權重，也可以算出最適合的 retention。重新擬合後，可以用每張卡的紀錄重新排程。
- 時間一律用 UTC。

## 證據（怎麼評估、數字、樣本多大）

- README 沒有評估數字。演算法的學術來源（Ye et al., KDD 2022 的間隔重複排程論文）這次沒有讀，只在 search-log 篩選。
- 專案活躍：py-fsrs 2026-08 有更新；Rust 版 fsrs-rs 2026-11-10 有更新（★ 460、BSD-3-Clause）。

## 對 AI TA：可以借用／不適用（原因）

- **可以借用：狀態分兩層存**（推論）：
  - **事件紀錄**（只新增、不修改）：每次出題、作答、批改結果、時間。對應 `ReviewLog`。
  - **衍生狀態**（可以隨時從紀錄重算）：每個知識點的掌握度、下次複習時間。對應 `Card`。

  好處是：之後換學習者模型（例如從計數改成 BKT）時，只要從紀錄重算，不會丟資料；也符合專案「records 只新增」的習慣。
- **可以借用：「卡片」換成「知識點」**。FSRS 的單位是一張卡片，AI TA 的單位可以是筆記的一個 H3 小節或「這節記住」。一個知識點可以出很多題，每題作答都更新同一個知識點的狀態（推論；同一知識點出不同題的效果，FSRS 沒有處理，需要 T3 判斷）。
- **可以借用：評分要先決定刻度**。FSRS 用 4 級自評；AI TA 由模型批改，要把「對／部分對／錯」對應到這 4 級，或改用 0–1 分數（推論）。
- **輕量、離線**：純 Python，不需要網路或 GPU，符合離線限制（推論，沒有安裝實測）。
- **不適用：預設權重的來源**。預設權重是從大量 Anki 使用者的資料擬合的，記的是單字、閃卡這類材料；概念理解題的遺忘曲線可能不同。使用者自己的紀錄要累積到一定量，才值得重新擬合（推論；最少要多少筆，README 沒說）。

## 限制與疑點

- 依任務規定沒有安裝，只讀了 README 和原始碼。
- 分級：開源專案、持續維護、授權清楚，屬 B 級；它對「這個工具能做什麼」是一手資料，但「這樣排程最好」要看 T3 的學習科學證據。

## T3：學習科學與排程（T3／T8 工作階段補充）

- **為什麼要間隔複習**：分散練習是讀書技巧中效果最大的一種（後設分析 d = 0.85，[2021-ten-learning-techniques-meta](../papers/2021-ten-learning-techniques-meta.md)）；美國教育部 IES 實務指南把「隔幾週到幾個月再複習重點」列為中等證據（[2007-ies-organizing-instruction](../papers/2007-ies-organizing-instruction.md)）。
- **最佳間隔取決於要記多久**：Cepeda et al. 2008（[2008-cepeda-spacing](../papers/2008-cepeda-spacing.md)）發現最佳間隔約是保留時間的 20%（記幾週）到 5%（記一年）。這門課沒有期末考，沒有固定的「考試日」，所以用 FSRS 這種「預測記得機率掉到目標值才複習」的排程，比固定比例更合理（推論）。
- **預設參數夠不夠用**：srs-benchmark（同一個組織維護，自家宣稱）用約 1 萬名 Anki 使用者、約 7.27 億次複習比較演算法。log loss（預測記得機率的誤差，越低越好）：FSRS-7 經個人化最佳化為 0.3401，FSRS-7 預設參數 0.3620，只用平均值的基準 0.3945。也就是說，預設參數已經比不用模型好，累積紀錄後再最佳化會更好（讀取 [srs-benchmark README](https://github.com/open-spaced-repetition/srs-benchmark)，2026-11-11）。最少要多少筆紀錄才值得最佳化，README 沒寫，**查不到**。
- **回答上面「同一知識點出不同題」的問題**：
  - IES 指南建議重考時**換一種問法**，學到的才是概念而不是某一題的答案；測驗效果也能跨題型（做填空題，考選擇題也會進步）。
  - 所以「一個知識點當一張卡、每次輪替不同題目」和學習科學一致；但 FSRS 的記憶模型是用「同一張卡反覆出現」的資料擬合的，換題後預測準不準，沒有證據（推論，待實測）。
- **評分刻度的建議**（推論）：批改用 SemEval-2013 的 5 類標籤（[2013-semeval-student-response](../papers/2013-semeval-student-response.md)），再對應到 FSRS 的 4 級：
  - 正確 → Good（使用者自評很有把握時可升為 Easy）。
  - 部分正確但不完整 → Hard。
  - 矛盾、離題、非領域（含「不知道」）→ Again。
- **評估提醒（T8）**：學生對自己學得多好的感覺不準（[2025-genai-guardrails-learning](../papers/2025-genai-guardrails-learning.md)），所以 Easy／Hard 不宜完全交給使用者自評，最好以批改結果為主。
