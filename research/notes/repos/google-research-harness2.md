---
title: "Harness²: Recursive Agent Harnessing for an Open World"
type: repo
tier: B
fit: 中
topics: [T4, T5]
year: 2026
venue: "google-research/harness2；GitHub ★ 23.4k；最後推送 2026-11-02；Apache-2.0；論文是 arXiv 2610.14224 預印本（Northwestern＋Google Cloud AI Research）"
url: https://github.com/google-research/harness2
self_reported: true
status: read
accessed: 2026-11-11
---
## 一句話

自動改良「agent 外殼」（harness）的研究框架：在沒看過的任務上提出外殼修改、在同一題上試跑比較，再組合出更好的外殼。它示範了「外殼怎麼拆、怎麼改」，但不是拿來直接做 agent 的工具，現成程式也不能在本機離線跑。

## 他們怎麼做

- **harness 的定義**：模型周圍讓它能當 agent 的整套系統，包括提示詞、工具、記憶、技能和協調流程。模型權重固定不動（Agent = Model + Harness）。
- **8 個可改元件，每個都是一個檔案**（論文 Table 5，沿用 AHE〔arXiv 2604.25850〕的「一個元件一個檔案」拆法）：

  | 群組 | 元件 | 檔案 | 何時進入模型 |
  |---|---|---|---|
  | 上下文 | 系統提示 | `systemprompt.md` | 每次呼叫 |
  | 上下文 | 護欄（guardrails，不論任務都要守的硬規則） | `guardrails.md` | 每次呼叫 |
  | 上下文 | 記憶（跨任務保留的領域事實） | `LongTermMEMORY.md` | 每次呼叫 |
  | 上下文 | 技能（skills，特定程序，用到才載入） | `skills/<n>/SKILL.md` | 呼叫 skill 工具時 |
  | 工具介面 | 工具說明（何時、怎麼用既有工具） | `tool_guidance.md` | 每次呼叫 |
  | 工具介面 | 腳本（確定性的程式，取代讓模型逐字推理） | `scripts/<name>.py` | 經 bash 執行 |
  | 協調 | 子代理（subagent，在自己的上下文裡做事，只回傳結果） | `sub_agents/<n>/AGENT.md` | task 工具 |
  | 中介層 | 外掛（plugin，包在工具呼叫外面的程式，強制行為而不是用提示詞要求） | `plugin/<name>.ts` | 工具迴圈內 |

- **兩層遞迴**：
  - 任務層「提出—試跑—組合」（Propose–Probe–Compose）：先跑一次參考執行；分別提出「通用」（規劃、工具使用、上下文管理）和「領域」兩種修改；在同一題、同一模型下試跑；比較行為差異（behavioral contrast）後組合成新外殼。全程不看標準答案。
  - 改良層：任務結束後把採用的外殼和「有執行證據支持」的經驗寫進一個函式庫（每筆附 `EXPERIENCE.md`），下一題提案時參考。
- **執行環境**：執行器是現成的 OpenCode 或 Codex；改外殼的「編輯器」和最後挑結果的「選擇器」都是 Claude Opus 4.8（高推理強度，跑在 OpenCode 裡）。每次執行最多 200 個模型回合、3,600 秒。

## 證據

- **主結果（作者自測，每組 3 次取平均）**：執行器是 GLM-5 和 Gemini 3.5 Flash，外殼是 OpenCode 和 Codex。只改一步就全部進步：WorkBuddy-Bench 最多 +11.5 分、JobBench +4.5 分、LAB 部分通過率 +11.8 個百分點。平行遞迴 k=5 再多 2.6–6.7。
- **同一模型自己改自己**（Figure 8）：GLM-5、Gemini 3.5／3.7 Flash、Claude Opus 4.8／5 都當自己的編輯器，五個都進步。結論是「不一定要更強的編輯器」，但被測的最弱模型 GLM-5 仍是大型雲端模型。
- **元件消融**（Table 6）：拿掉技能平均少 5.3 分、拿掉腳本少 3.7、拿掉提示類元件少 1.5；拿掉函式庫、範圍分工、組合步驟也都會退步（Table 3）。
- **工具使用可靠度**（Table 7）：工具錯誤率全部下降，例如 JobBench 14.4% → 9.1%。
- **和現成外殼比**（Figure 13）：同一個 Gemini 3.5 Flash 放進 CodeBuddy、OpenCode、Codex、Claude Code，沒有一個外殼在所有領域都最好；同一模型換外殼差幾分。
- **個案**（Figure 9、15–19）：失敗多半是「程序」問題，不是知識不足。例如沒交叉核對檔案、寫完不回頭檢查；有一例是模型把工具呼叫寫成純文字、沒有真的執行，在 `tool_guidance.md` 禁止這種「假呼叫」後從 60 分變 100 分。
- **成本**：Figure 6 的橫軸是「每題總運算量（百萬 token，對數刻度）」，含執行與改良成本，各方法都落在百萬 token 等級。論文自己承認遞迴改良會增加推論成本。

## 對 AI TA：可以借用／不適用

- **可以借用**：
  - 8 個元件的拆法和「一個元件一個檔案」的做法，可以直接當 `dev/harness/` 的資料夾結構，改動就是 diff，好追蹤。
  - 「改了就測、比較再決定」的方法：用評估題組手動做（qwen3.5:9b 當執行器，我當編輯器；開發期要不要讓 frontier 模型當編輯器，待使用者決定），不需要它的程式。
  - 個案的教訓：把「回頭檢查」寫成腳本或外掛強制執行，比在提示詞裡要求更可靠；工具說明要明講「不要把呼叫寫成文字」（本機實驗也看到 9B 有類似問題，見 [本機實驗](../internal/2026-local-qwen35-tool-calling.md)）。
- **不適用**：
  - **不能直接在本機離線跑**（`docs/SETUP.md`，2026-11-11 讀）：需要 Linux、Google Cloud CLI、Vertex AI 認證；評審模型 ID 由程式自動加上 Vertex 前綴；改良器只支援 Vertex 上的 Claude 或 Gemini；WorkBuddy 還要 Docker。執行器理論上可以換：OpenCode 用 `provider/model` 格式指定模型，Codex 可以設 `HARNESS2_CODEX_BASE_URL` 指向任何 Responses API 端點；但評審和改良器仍綁 Vertex，而且沒有 Ollama 或 macOS 的說明（推論：要接本地模型得改程式）。
  - 每題百萬 token 等級的成本，用 9B 在 M5 上跑會非常慢（推論：本機實驗量到冷啟動預填約每秒 250 token、生成約每秒 10 token）。
  - 它的基準測試（JobBench、LAB、WorkBuddy-Bench）跟課程複習無關。

## 限制與疑點

- 數字都是作者自測；評分大量用 LLM 評審（Gemini 3.5 Flash、Claude Opus 4.8、Claude Sonnet 4.6）。
- 沒有任何 7–9B 模型的實驗，「同一模型自己改自己也有效」能不能延伸到 9B 是未知數。
- 執行器的網路不受限制，Codex 在沙箱關閉的狀態下執行，自己跑之前要注意安全。
- 星數與推送日期是 2026-11-11 讀取時的數字。論文 PDF 存在 `research/pdfs/google-research-harness2.pdf`。

> 來源：原本記在 `參考 repo.md` 的連結，已併入本筆記。2026-11-11 由 T4／T5 工作階段補讀論文本文（arXiv 2610.14224v1）與 `docs/SETUP.md`，狀態從 screened 改為 read。
