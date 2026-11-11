---
title: "Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models"
type: paper
tier: A
fit: 高
topics: [T5]
year: 2024
venue: "EMNLP 2024 Industry Track（2024.emnlp-industry.91，pp. 1218–1236）；Appier AI Research＋臺大"
url: https://aclanthology.org/2024.emnlp-industry.91/
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

強制模型輸出 JSON 等格式，會讓**推理題**變差，越嚴格的限制退步越多；但**分類題**反而可能變好。先用自然語言回答、再轉成格式，幾乎不損失。

## 他們怎麼做

- **三種限制強度**：
  1. JSON mode（受限解碼，constrained decoding：解碼時只允許產生合法 JSON 的 token）。
  2. 格式指示（FRI）：在提示裡要求用 JSON／XML／YAML 回答。
  3. NL-to-Format：先自由回答，再叫模型把答案轉成指定格式（最寬鬆）。
- **任務**：推理類（GSM8K 數學、Last Letter 字母串接、Shuffled Objects 狀態追蹤）；分類類（DDXPlus 醫療診斷、MultiFin、Sports、NI Task 280）。
- **模型**：GPT-3.5-turbo、Claude-3-Haiku、Gemini-1.5-Flash，以及開源的 **LLaMA-3-8B-Instruct、Gemma-2-9B-Instruct**。
- 為了排除「解析錯誤」的干擾，用另一個 LLM 當「完美解析器」抽答案；每個設定用 9 種提示組合測，看平均和變異。

## 證據

- **推理題**：JSON mode 通常最差，其次是格式指示，NL-to-Format 和自由回答幾乎一樣。例：GPT-3.5 在 Last Letter 的 JSON mode 輸出 100% 把 `answer` 放在 `reason` 前面，等於沒做推理就先給答案。
- **schema 越細越糟**（Table 1，GSM8K）：在提示裡附上具體 schema，LLaMA-3-8B 的 JSON 從 64.67 降到 48.90，且變異變大。
- **分類題**：JSON mode 不一定差，有時更好（例如 Gemini-1.5-Flash 在 DDXPlus 明顯提升），作者推測是限制了答案空間。
- **不是解析錯誤造成的**：Gemini-Flash、GPT-3.5 幾乎沒有解析錯誤，分數仍下降；LLaMA-3-8B 的 XML／YAML 解析錯誤較多，但用「第二個提示修正格式」就能補救。
- 較新的 gpt-4o-mini 結構化輸出（JSON-Schema）在 3 個推理資料集中仍有 2 個不如自由回答。

## 對 AI TA：可以借用／不適用

- **可以借用**：
  - **分開「想」和「填表」**：解釋、判斷錯因這種推理步驟，先讓模型自然語言（或在思考模式裡）想完，再要求結構化輸出；或兩步走（NL-to-Format）（推論）。
  - **欄位順序**：schema 裡把 `reasoning` 放在 `answer` 前面（論文找到的失敗原因之一）。
  - **批改結果是分類題**（對／錯、錯誤類型），用嚴格 schema 是合理的，甚至可能更準（推論，依分類任務的結果）。
  - 格式錯了用「第二個提示修正」比整題重來便宜。
- **要注意**：
  - qwen3.5 的思考模式把推理放在 `thinking` 欄位、和 `content` 分開，可能天然避開「先給答案」的問題；但開思考會大幅變慢（推論，[本機實驗](../internal/2026-local-qwen35-tool-calling.md) E4 有測速度）。

## 限制與疑點

- **有爭議**：結構化生成套件的公司 .txt 發表反駁〈[Say What You Mean](https://blog.dottxt.ai/say-what-you-mean.html)〉，認為退步來自提示設計和評估方式，不是結構本身（C 級，廠商立場，未經同儕審查）。目前判斷：「嚴格格式可能傷推理」是**互相矛盾**的主張，條件是提示設計；但兩邊都同意「推理在前、答案在後」和「寬鬆格式較安全」。
- 用的模型是 2024 年版本；qwen3.5 未測。
- PDF 存在 `research/pdfs/2024-let-me-speak-freely.pdf`。
