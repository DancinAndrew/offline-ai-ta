---
title: "ReAct: Synergizing Reasoning and Acting in Language Models"
type: paper
tier: A
fit: 中
topics: [T4, T5]
year: 2023
venue: "ICLR 2023（iclr.cc 會議頁：poster 11003；arXiv 2210.03629 v3 為 camera-ready）；Princeton＋Google"
url: https://iclr.cc/virtual/2023/poster/11003
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

讓模型交替產生「想法」（reasoning trace）和「動作」（呼叫工具），用工具結果修正推理。這是今天多數 agent 外殼「想—做—看結果」迴圈的源頭；但論文也顯示：**小模型只靠提示學不會 ReAct，要微調才行**。

## 他們怎麼做

- **想法**：把模型的動作空間加上「語言」：想法不改變環境，只用來拆目標、追蹤進度、處理例外、調整計畫。
- **任務**：
  - 知識型：HotpotQA（多跳問答）、FEVER（事實查核），工具是簡化的 Wikipedia API（search、lookup、finish）。
  - 決策型：ALFWorld（文字遊戲）、WebShop（網購）。
- **模型**：主要是凍結的 PaLM-540B，用 1–6 個人工示範（few-shot）提示；另外用 3,000 條正確軌跡微調 PaLM-8B、62B。
- **組合策略**：ReAct 和 CoT-SC（多次推理取多數）互相備援：ReAct 幾步內沒答案就改用 CoT-SC；CoT-SC 意見分歧就改用 ReAct。

## 證據

- **知識型**（PaLM-540B，Table 1）：HotpotQA EM：Standard 28.7、CoT 29.4、Act 25.7、ReAct 27.4、ReAct→CoT-SC 35.1（最好）。FEVER：ReAct 60.9 > CoT 56.3；CoT-SC→ReAct 64.6（最好）。
- **錯誤型態**（HotpotQA，人工標註 200 例，Table 2）：CoT 失敗中 56% 是幻覺（編造事實）；ReAct 幾乎沒有幻覺（0%），但 47% 是推理錯誤，其中常見的是**重複前面的想法和動作、跳不出迴圈**；23% 是搜尋沒拿到有用資訊。
- **決策型**：ALFWorld 最好一次 71%（Act 45%、模仿學習 BUTLER 37%）；WebShop 成功率 40.0%（Act 30.1%）。
- **規模與微調**（Figure 3，HotpotQA）：
  - 只用提示時，PaLM-8B／62B 的 ReAct 是四種方法中**最差**的，作者說小模型難以從少量示範同時學會推理和行動。
  - 用 3,000 條軌跡微調後，ReAct 變成最好：微調的 8B ReAct 勝過所有 62B 的提示方法；微調的 62B 勝過所有 540B 的提示方法。

## 對 AI TA：可以借用／不適用

- **可以借用**：
  - 「從環境拿到真實結果再推理」能壓低幻覺：AI TA 回答前先檢索講義（等於 ReAct 的 search），比純靠模型記憶可靠（與 T2 的 RAG 方向一致）。
  - ReAct 的主要失敗是**迴圈重複**和**檢索失敗後卡住**：AI TA 的流程要設步數上限，檢索沒結果時由程式改寫查詢或直接說「講義沒有」（推論）。
  - 「兩種方法互相備援」的想法：例如先檢索作答，檢索分數太低才退回模型自己的知識並標明（推論）。
- **不適用／要注意**：
  - 用的是 2022 年的 PaLM，模型沒有原生工具呼叫；今天的 qwen3.5:9b 已用大量 agent 環境訓練（模型卡自述），「小模型提示學不會 ReAct」不能直接套用，但「小模型自主規劃較弱」的方向仍有 [BFCL](2025-bfcl.md) 多輪結果佐證（推論）。
  - Qwen 官方文件明確**不建議**對 Qwen3 這類推理模型用 ReAct 那種「停止詞」格式的工具呼叫範本，因為模型可能在思考段落裡輸出停止詞，造成誤判（見 [Qwen-Agent 筆記](../repos/QwenLM-Qwen-Agent.md)）。要用模型原生的工具呼叫格式。

## 限制與疑點

- HotpotQA 子集只有部分題目；工具（Wikipedia API）刻意做得很弱，用來逼模型推理。
- OpenReview 頁面有瀏覽器驗證，無法用工具開啟；刊登資訊以 iclr.cc 的會議頁為準。
- PDF 存在 `research/pdfs/2023-react.pdf`。
