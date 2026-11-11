---
title: "Large Language Models Cannot Self-Correct Reasoning Yet"
type: paper
tier: A
fit: 高
topics: [T5]
year: 2024
venue: "ICLR 2024（iclr.cc 會議頁：poster 18956）；Google DeepMind＋UIUC；arXiv 2310.01798"
url: https://iclr.cc/virtual/2024/poster/18956
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

沒有外部回饋時，叫模型「檢查並修正自己的答案」（內在自我修正）不會變好，常常變差；過去說自我修正有效的研究，多半偷偷用了標準答案決定何時停止。

## 他們怎麼做

- **定義**：內在自我修正（intrinsic self-correction）＝只靠模型自己判斷，不用標準答案、人類或工具的回饋。
- **流程**：先回答 → 叫模型檢查並給回饋 → 依回饋重答，最多兩輪。
- **資料與模型**：GSM8K（數學）、CommonSenseQA（常識選擇題）、HotpotQA；GPT-3.5-Turbo、GPT-4、GPT-4-Turbo、Llama-2-70B-chat。另試三種不同的檢查提示。

## 證據

- **有標準答案時**（Table 2）：GPT-3.5 的 GSM8K 75.9 → 84.3。但這要先知道答案對不對，實際上不可能。
- **沒有標準答案時**（Table 3、4）：全部模型、全部資料集都下降。例：
  - GPT-3.5，CommonSenseQA：75.8 → 38.1（第一輪）。
  - Llama-2-70B，GSM8K：62.0 → 43.5 → 36.5；CommonSenseQA：64.0 → 37.5。
  - GPT-4，GSM8K：95.5 → 91.5 → 89.0。
- **為什麼變差**（Figure 1）：模型無法可靠判斷自己的推理對不對；修正時「對改成錯」比「錯改成對」多。Llama-2 在 GSM8K 有 31% 的題目從對改成錯；GPT-4 系列比較常維持原答案。
- 換不同的檢查提示（Table 5、6）也一樣下降。
- 多代理辯論（多個同模型互相批評）在相同的呼叫次數下，不比「多次取樣取多數」（self-consistency）好。

## 對 AI TA：可以借用／不適用

- **可以借用**：
  - **驗證迴圈一定要有外部依據**：AI TA 的檢查步驟要對照講義原文、題目的標準答案、或程式可檢查的規則（JSON 格式、選項數、出處編號存在），而不是叫 qwen3.5:9b「再檢查一次」（推論；有外部工具回饋時自我修正有效，見同屆 ICLR 的 CRITIC，arXiv 2305.11738，只篩選）。
  - **越弱的模型越容易把對的改錯**（Llama-2 vs GPT-4）：9B 做無依據的自我修正風險更高（推論）。
  - 相同運算預算下，「多次取樣取多數」是比「辯論」更划算的基線，可用在批改這種有固定答案的判斷（推論）。
- **不適用**：測的是數學、常識推理；「出題品質」「解釋是否清楚」這類沒有單一答案的輸出，論文沒測。

## 限制與疑點

- 模型是 2023 年版本；有思考模式的新模型（例如 qwen3.5）在思考段落裡本來就會自我檢查，結論是否改變未知。
- OpenReview 頁面有瀏覽器驗證，無法用工具開啟；刊登資訊以 iclr.cc 的會議頁為準。
- PDF 存在 `research/pdfs/2024-llms-cannot-self-correct.pdf`。
