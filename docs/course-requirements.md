# 課程對 AI TA 的要求

機器學習課（中央大學，林家瑜教授，2026 Fall）貫穿整學期的專題：自己做一個 **AI 助教（AI TA）**，用它來複習、出題、給實作練習，並和它合作完成 AI Cup 與期末專題。

> 整理自課程資料（2026-10-19，2026-11-11 更新），規格以教授最新公告為準。這份只記課程端的要求；本專案自己的目標與步驟見 [plan.md](plan.md)。

## 課綱的要求

課綱 p.9「The Teaching Method of Class」：

- 自己建 AI TA，從中學生成式 AI 技能，而且**要建本地模型（local model）**。
- 讓 AI TA 幫你學習：複習（review）、出小考（quiz）、給實作練習（implementation practice）。
- 和 AI TA 合作完成作業與任務。

Week 2 課堂補充（教授口述）：基礎模型（foundation model）是通用的，只用它的話，每個人的 AI TA 都一樣。要餵最新論文或特定領域資料（微調或外接知識）讓 AI TA 個人化，它才會懂最新模型，也才會跟別人不同。

## 配分（相關項目）

| 項目 | 比重 | 內容 |
|---|---|---|
| AI TA Building | 30% | How to train AI TA 15% ＋ AI Cup Competition 15%（上傳 AI 互動紀錄，依班內排名） |
| Final Project | 25% | 主題：Personalized and Extended Functions of AI TA |
| Netflix HW | 15% | 交 AI 互動紀錄與分析結果（在 `Machine Learning/HW2-Netflix_ML/`） |
| Bonus | 最多 2% | Share the AI Cup Progress |

期末專題細節（課綱 p.22–26）：

- 4 人一組（人類），英文報告，簡報加 2 分鐘影片。
- 需上傳 AI 互動紀錄，並做 AI TA 的延伸功能（extension functions）。
- 評分：Report 25%、Presentation 20%（同儕排名）、Originality 15%、Performance 20%、Presentation video 20%。Most Popular Award 前三名加 8／5／3 分。

**「How to train AI TA（15%）」的繳交形式與評分標準，課綱沒寫；截至 2026-11-11 仍無新消息。**

這門課沒有期末考。

## 時程

> 教授已重新排程，下表是原課綱的安排，實際上課時間未定。截至 2026-11-11，LLM、RAG、Ollama 都還沒上。

| 週 | 日期 | 和 AI TA 有關的內容 |
|---|---|---|
| 7 | 10/19 | LLM、RAG、**Build Ollama Model**（起點） |
| 13 | 11/30 | Interface、AI Agent；**把介面／AI agent 加進 AI TA** |
| 15 | 12/14 | 分享如何在 AI Cup 中和 AI TA 合作；**繳交期末專題** |
| 16 | 12/21 | 期末專題同儕互評 |

## AI Cup（AI TA Building 的一半分數）

- 題目：結合少樣本學習、資料生成與多模態視覺語言模型（VLM）之太陽能板瑕疵檢測與根因分析。
- 個人參賽（一人一隊），依班內排名給分。
- 可用任何 AI 工具，但**要開新的 chat session**，比賽結束後教授會收聊天紀錄。
- 報名流程：AI CUP 報名系統建隊 → AIdea 平台（同一 email）→ 等 1–2 個工作天開通 → 填隊號回報表單。
- 期限：報名 2026/11/16 23:59:59 截止，結果提交 2026/12/04 23:59:59 截止（UTC+8）。
- 比賽本身在另一個專案 `Machine Learning/AICUP2026/`。

## 來源

以下是本機路徑，在 GitHub 上打不開。

- [課綱 Syllabus](../../Week1/1.%20Syllabus.pdf)：p.9 教學方式、p.11 時程、p.19 配分、p.22–26 期末專題
- [AI Cup 報名規則](../../Week7/課程PPT/AICUP2026_Registration_Rules.pdf)
- [AICUP2026 專案 README](../../AICUP2026/README.md)：比賽時程
- [Week 2 筆記：Introduction to AI & ML](../../Week2/機器學習%20Week2：Introduction%20to%20AI%20&%20ML.md)：第 167 行，AI TA 個人化
- [HW2 Netflix](../../HW2-Netflix_ML/)：同樣要交 AI 互動紀錄
- 參考案例（另一門課）：[AIASE 2026 W1 課程介紹](../../../Engineering/10_AI/課程-AIASE%202026/W1_課程介紹、修課要求與評分方式.md)、[W6 AI Application](../../../Engineering/10_AI/課程-AIASE%202026/W6_AI_Application.md)。該課用 Discord 上的 AI 助教 agent 回答問題，也嘗試用 AI 評分。
