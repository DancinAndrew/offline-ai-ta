---
title: "Anki 官方手冊：複習流程、作答按鈕、Leech、FSRS 期望記憶率、公式"
type: doc
tier: A
fit: 高
topics: [T7, T3]
year: 2026
venue: "Anki 手冊（ankitects/anki-manual，最後更新 2026-10-06；網站版 docs.ankiweb.net）；用 gh api 讀 src/studying.md、leeches.md、deck-options.md、math.md"
url: https://github.com/ankitects/anki-manual/blob/main/src/studying.md
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

Anki 的複習介面成熟且文件完整：先看題目、自己想、再翻答案，用 Again／Hard／Good／Easy 四個按鈕自評；一直忘記的卡片自動標成 **leech**。這套流程可以直接借給 AI TA 的測驗模式和錯題本。

## 他們怎麼做（文件說了什麼）

- **複習流程**（studying）：
  - 牌組總覽顯示今天要複習幾張（新卡、學習中、待複習）→ 按「Study Now」。
  - 先只顯示問題 → 想好後按「Show Answer」或空白鍵 → 對照答案、按按鈕。
  - 手冊建議：想超過約 10 秒，就直接看答案。
- **四個按鈕**：
  - Again：答錯或想不起來；部分正確也應該嚴格算錯。
  - Hard：答對，但猶豫或想很久。
  - Good：答對，有花一點力氣；正常應該佔 80–95%。
  - Easy：不費力就答對。
  - 也可以只用 Again 和 Good 兩個。每個按鈕上會顯示「選它的話下次什麼時候再出現」。
- **FSRS**（deck-options）：**FSRS**（Free Spaced Repetition Scheduler：依每張卡的作答紀錄，預測多久後會忘，在快忘時排複習）。
  - 最重要的設定是**期望記憶率**（desired retention：卡片到期複習時答得出來的機率），預設 90%。超過 90% 工作量快速上升，超過 97% 會多到難以負荷。
  - 手冊特別提醒：**忘記了卻按 Hard，排程會被高估**，因為 FSRS 把 Hard 當作「答對」。
- **Leech**（leeches）：**leech**（「吸血卡」：反覆忘記、吃掉大量複習時間的卡片）。
  - 一張卡在複習中答錯累積 8 次，就自動加上 leech 標籤並暫停；之後每再錯 4 次提醒一次。門檻可以調。
  - 手冊建議的處理方式是**改寫卡片**：拆成更小的概念、加例子、先真正理解，而不是一直重複。
- **公式**（math）：Anki 2.1 以上內建 MathJax，卡片可以寫 TeX。

## 證據

- 官方手冊只說明工具怎麼運作，不是學習成效證據。FSRS 的成效證據屬於 T3（排程演算法另見 [open-spaced-repetition-py-fsrs](../repos/open-spaced-repetition-py-fsrs.md)）。

## 對 AI TA：可以借用／不適用（原因）

- **可以借用（T7 互動設計）**：
  - **測驗模式**：出題 → 使用者先作答 → 才顯示參考答案和出處。和 PNAS 研究的「先作答、再給提示」一致（見 [2025-genai-guardrails-learning](../papers/2025-genai-guardrails-learning.md)）。
  - **AI 批改只給「錯／對」兩級**，對應 Again／Good，避免把「錯」記成 Hard 而污染排程（推論，依手冊對 Hard 的警告）。
  - **錯題本 = leech 的概念**：同一個概念錯到門檻就進錯題本；處理方式是重新解釋、拆小、換例子，而不是同一題一直考（推論）。
  - **每題顯示「下次什麼時候再考」**，讓使用者知道排程。
- **不適用**：
  - Anki 是另一個 App。AI TA 要嘛把題目匯出給 Anki 排程，要嘛自己實作 FSRS；兩條路都要在開發階段決定。

## 限制與疑點

- 這門課期中之後沒有期末考。複習目標是「長期記住」還是「某一天考試」，會影響期望記憶率怎麼設；手冊沒有答案（T3）。
