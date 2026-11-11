---
title: "Building effective agents（Anthropic 工程文章）"
type: article
tier: B
fit: 高
topics: [T4, T5]
year: 2024
venue: "Anthropic Engineering（2024-12-19 發表；2026-11-11 讀取時頁首加註「工具生態自 2024 年 12 月以來已大幅改變」）"
url: https://www.anthropic.com/engineering/building-effective-agents
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

把「agentic 系統」分成兩類：**workflow**（LLM 和工具照預先寫好的程式路徑走）和 **agent**（LLM 自己決定流程和要用哪些工具）。建議先用最簡單的做法，只有證明有效才加複雜度。

## 他們怎麼做

- **定義**：
  - Workflow：LLM 和工具由預先定義的程式路徑協調。
  - Agent：LLM 動態決定自己的流程與工具使用，對怎麼完成任務保有控制權。
- **基本單元「增強的 LLM」**：LLM 加上檢索、工具、記憶。
- **五種 workflow 模式**：
  1. 提示鏈（prompt chaining）：拆成固定步驟，每步處理上一步的輸出，中間可以加程式檢查（gate）。適合能乾淨拆成固定子任務的工作，用延遲換正確率。
  2. 路由（routing）：先分類，再交給專門的提示或模型。
  3. 平行化（parallelization）：拆段平行做，或同一題做多次投票。
  4. 協調者—工作者（orchestrator-workers）：中央 LLM 動態拆任務，子任務事先不固定。
  5. 評估者—最佳化者（evaluator-optimizer）：一個產生、一個評估回饋，迴圈改進。適合「有清楚評估標準」的情況。
- **Agent**：本質是「LLM 在迴圈裡根據環境回饋使用工具」；每一步都要從環境拿到「實際結果」（ground truth，例如工具結果）來判斷進度。適合步數無法預測、不能寫死路徑的開放問題；代價是成本高、錯誤會累積。
- **框架**：框架容易起步，但會多一層抽象，讓提示和回應難以除錯。建議先直接呼叫 API，很多模式幾行程式就能做；用框架就要看懂底層。
- **工具設計（附錄 2）**：工具說明要像寫給新進工程師的文件；格式貼近網路上常見的文字；避免要求模型精確計數或跳脫字元；「防呆」設計參數（例如改成必須用絕對路徑後，錯誤消失）。他們做 SWE-bench 時花在工具上的時間比花在整體提示上多。

## 證據

- 經驗性指南，依據是「與數十個團隊合作的經驗」，沒有對照實驗或數字。
- 例子是 Claude 系列大模型，沒有小模型。

## 對 AI TA：可以借用／不適用

- **可以借用**：
  - 「workflow 與 agent」的分法直接對應 AI TA 的設計選擇：複習流程（找弱點 → 出題 → 批改 → 解釋 → 安排下次）步驟固定，符合「能乾淨拆成固定子任務」的提示鏈條件；只有「自由追問」比較像開放問題（推論）。
  - 提示鏈中間加程式檢查（gate）：例如出題後用程式驗證 JSON、選項數、出處編號存在，不合格就重來。
  - 評估者—最佳化者的前提是「有清楚的評估標準」；批改有答案和講義可以對照，符合；開放式解釋則較弱（推論）。
  - 工具設計原則（清楚的說明、防呆參數）對 9B 更重要，因為小模型更容易誤用工具（推論，佐證見 [α-UMi](../papers/2024-small-llms-weak-tool-learners.md)、[本機實驗](../internal/2026-local-qwen35-tool-calling.md)）。
- **不適用／要注意**：文中「agent 適合的條件」以 Claude 等級的模型為前提；對 9B 模型，「信任它的決策」這個條件更難成立（推論）。

## 限制與疑點

- 2024 年 12 月的文章，頁首已註明工具生態大幅改變；但 workflow／agent 的分類與「從簡單開始」的原則沒有被撤回。
- 屬於大型 AI 實驗室的工程指南（B 級），不是同儕審查研究；結論需要其他來源佐證（LangGraph 官方文件〔[Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)〕採用同樣的分法，但那是同一套概念的轉述，不算獨立證據）。
