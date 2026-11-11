---
title: "Harness²: Recursive Agent Harnessing for an Open World"
type: repo
tier: B
fit: 中
topics: [T4, T5]
year: 2026
venue: "google-research/harness2；GitHub ★ 23.2k；Apache-2.0；論文是 arXiv 2610.14224 預印本"
url: https://github.com/google-research/harness2
self_reported: true
status: screened
accessed: 2026-11-09
---
## 一句話

自動改良「agent 外殼」（harness）的研究框架。它在沒看過的任務上提出外殼修改、試跑比較，再組合出更好的外殼。它不是拿來直接做 agent 的工具。

## 他們怎麼做

- **harness 的定義**：模型周圍讓它能當 agent 的整套系統，包括提示詞、工具、記憶、技能和協調流程。
- **可改的 8 個元件**：系統提示、護欄（guardrails；限制 agent 不能做什麼的規則）、記憶、工具說明、子代理、技能、腳本、外掛。
- **兩層遞迴**：
  - 任務層「提出—試跑—組合」（Propose–Probe–Compose）：提出修改，在同一個任務上試跑，比較不同版本的行為差異，再組合出新外殼。這個過程不需要標準答案。
  - 改良層：把採用的外殼和有證據支持的經驗，累積到一個持續更新的「改良用外殼」。
- **執行環境**：預設用 OpenCode 當執行器，可改用 Codex；模型透過 Google Vertex AI。

## 證據

- 作者自己測：只做一步改良，就讓 GLM-5 和 Gemini 3.5 Flash 進步。WorkBuddy-Bench 最多 +11.5 分、JobBench +4.5 分、LAB 部分通過率 +11.8 個百分點。這些是自家宣稱，未經獨立驗證。
- 測的都是大型雲端模型，沒有 9B 本地模型的數據。

## 對 AI TA：可以借用／不適用

- **可以借用**：
  - 8 個元件的拆法，可以當 `dev/harness/` 的分類方式。
  - 「改了就測、比較再決定」的方法，可以用自己的評估題組手動做。
- **不適用**：
  - 程式綁 Vertex AI 和 gcloud，README 只寫 Linux，沒提 Ollama 或本地模型。
  - 它的基準測試（JobBench、LAB、WorkBuddy-Bench）跟課程複習無關。

## 限制與疑點

- 目前只讀了 README，論文本文還沒讀，T4 研究時補。
- README 說 `docs/SETUP.md` 有「其他認證方式」，但還沒讀，所以不確定能不能接 OpenAI 相容的端點（Ollama 有提供這種端點）。
- 執行器的網路不受限制，Codex 也是在沙箱關閉的狀態下執行，跑之前要注意安全。
- 星數是 2026-11-09 讀取時的數字。

> 來源：原本記在 `參考 repo.md` 的連結，已併入本筆記。
