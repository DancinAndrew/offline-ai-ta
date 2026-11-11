# 來源總表

共 57 份筆記：A 權威 41、B 參考 13、C 線索 0、內部資料 3。每區依第一個主題、再依年份排列。等級定義見 [README.md](README.md) 第 3 節，跨主題結論見 [synthesis/summary.md](synthesis/summary.md)。

這份總表由筆記的屬性區產生；要改等級或主題，改筆記本身。

## A 權威

| 來源 | 類型 | 年份 | 主題 | 適用度 | 一句話 |
|---|---|---|---|---|---|
| [Jill Watson: A Virtual Teaching Assistant powered by ChatGPT](notes/papers/2024-jill-watson-chatgpt.md) | 論文 | 2024 | T1、T2 | 中 | 喬治亞理工的新版 Jill Watson 不微調模型，而是把流程拆成「補全問題 → 分類 → 依講義回答 → 檢查回答有沒有根據」幾個小步驟，每一步都是一個提示。 |
| [Ruffle&Riley: Insights from Designing and Evaluating a Large Language Model-Based Conversational Tutoring System](notes/papers/2024-ruffle-riley.md) | 論文 | 2024 | T1、T7、T3 | 中 | 從一篇課文自動產生「題目 + 答案要點」的教學腳本，再讓兩個 GPT-4 角色帶學生：學生把概念「教」給虛擬同學 Ruffle，需要時找虛擬教授 Riley。 |
| [Teaching CS50 with AI: Leveraging Generative Artificial Intelligence in Computer Science Education](notes/papers/2024-cs50-ai.md) | 論文 | 2024 | T1、T2 | 中 | 哈佛 CS50 自建「CS50 Duck」：所有 AI 工具共用一個後端，把學生的問題包進課程專屬的系統提示，再送到 Azure 上的 GPT-4；論壇問答另外用講課字幕做檢索。 |
| [AI tutoring outperforms in-class active learning: an RCT introducing a novel research-based design in an authentic educational setting](notes/papers/2025-ai-tutoring-outperforms-active-learning.md) | 論文 | 2025 | T1、T3 | 中 | 哈佛物理課的交叉設計隨機實驗（194 人）：照教學原則設計、提示詞裡附上老師寫好的逐步解答的 GPT-4 家教，學生用比較短的時間，學到的比課堂主動學習多（後測中位數 4.5 vs 3.5）。 |
| [Generative AI without guardrails can harm learning: Evidence from high school mathematics](notes/papers/2025-genai-guardrails-learning.md) | 論文 | 2025 | T3、T8、T1 | 高 | 近 1,000 名高中生的隨機對照實驗：練習時可以用一般 GPT-4 的學生，之後不能用 AI 的考試**退步 17%**；同樣用 GPT-4，但提示詞要求「只給提示、不給答案」並附上老師寫的解法與常見錯誤的版本，考試成績和對照組相同。 |
| [Enabling Large Language Models to Generate Text with Citations (ALCE)](notes/papers/2023-alce.md) | 論文 | 2023 | T2、T8 | 高 | 第一個能自動評估「模型回答有沒有附對出處」的基準（ALCE）。 |
| [Dense X Retrieval: What Retrieval Granularity Should We Use?](notes/papers/2024-dense-x-retrieval.md) | 論文 | 2024 | T2 | 中 | 切段的「大小」本身就會明顯影響檢索：把語料切成一句一個事實的「命題」（proposition）來建索引，比切成 100 字的段落更容易找到答案，放進提示詞時也更省篇幅。 |
| [Fine-Tuning or Retrieval? Comparing Knowledge Injection in LLMs](notes/papers/2024-fine-tuning-or-retrieval.md) | 論文 | 2024 | T6、T2 | 高 | 在 7B 模型上比較「微調」和「RAG」哪個比較能讓模型學會一批知識：RAG 在每個設定都勝出；對模型沒看過的新知識，微調幾乎沒幫助，有時還變差；同一個事實用很多種說法重複訓練才有改善。 |
| [M3-Embedding: Multi-Linguality, Multi-Functionality, Multi-Granularity Text Embeddings Through Self-Knowledge Distillation (BGE-M3)](notes/papers/2024-bge-m3.md) | 論文 | 2024 | T2 | 高 | BAAI 的多語嵌入模型 BGE-M3：一個模型同時給出三種檢索分數，支援 100 多種語言、最長 8,192 token。 |
| [RAFT: Adapting Language Model to Domain Specific RAG](notes/papers/2024-raft.md) | 論文 | 2024 | T6、T2 | 中 | 如果一定要微調，就用「開書考試」的方式訓練：每筆訓練資料都附上正確文件和干擾文件，要模型引用正確文件的原句、寫出推理再作答。 |
| [Obsidian 官方文件：CLI 與 Vault API（外部程式怎麼讀筆記的原始 Markdown）](notes/web/2026-obsidian-cli-vault-api.md) | 文件 | 2026 | T7、T2 | 高 | Obsidian 的 vault 就是一個裝 `.md` 檔的資料夾：外掛透過 Vault API 讀到的是原始 Markdown，官方 CLI（1.12.7 起）也能 `read`、`search`。 |
| [Ollama 官方模型庫與文件：嵌入模型、/api/embed、判斷模型（decision）](notes/web/2026-ollama-embedding-models.md) | 文件 | 2026 | T2 | 高 | Ollama 官方模型庫目前有十幾個可離線跑的嵌入模型，其中標明支援多語（含中文）的主要是 bge-m3、qwen3-embedding、embeddinggemma（1 與 2 代）、nomic-embed-text-v2-moe、snowflake-arctic-embed2。 |
| [Open WebUI 離線模式（官方文件站：離線教學與環境變數參考）](notes/web/2026-open-webui-offline.md) | 文件 | 2026 | T7、T2 | 中 | Open WebUI 是功能最完整的本機網頁聊天介面，可以離線使用，但要先在有網路時把嵌入模型等快取好；`OFFLINE_MODE` 只關掉更新檢查和模型下載，**不會擋住其他對外連線**，真正隔離要靠防火牆或斷網。 |
| [Organizing Instruction and Study to Improve Student Learning (IES Practice Guide, NCER 2007-2004)](notes/papers/2007-ies-organizing-instruction.md) | 文件 | 2007 | T3 | 高 | 美國教育部研究單位請記憶與學習研究者組成小組，把「怎麼安排教學和讀書時間」整理成 7 條建議，每條都標了證據等級。 |
| [Spacing Effects in Learning: A Temporal Ridgeline of Optimal Retention](notes/papers/2008-cepeda-spacing.md) | 論文 | 2008 | T3 | 中 | 兩次學習之間隔多久最好，取決於「要記多久」：要記幾週，最佳間隔約是保留時間的 20%；要記一年，降到約 5%。 |
| [SemEval-2013 Task 7: The Joint Student Response Analysis and 8th Recognizing Textual Entailment Challenge](notes/papers/2013-semeval-student-response.md) | 論文 | 2013 | T3、T8 | 中 | 一個經典的「批改學生簡答」共享任務：給題目、參考答案和學生答案，把學生答案分成 5 類：**正確、部分正確但不完整、與參考答案矛盾、離題、和領域無關**。 |
| [The Power of Feedback Revisited: A Meta-Analysis of Educational Feedback Research](notes/papers/2020-feedback-meta-analysis.md) | 論文 | 2020 | T3 | 中 | 回饋平均有中等效果（d = 0.48），但差異極大：只說對錯或給獎懲效果小（d = 0.24），附上正確答案效果中等（d = 0.46），**同時說明錯在哪、怎麼想、怎麼監控自己**的「高資訊回饋」效果最大（d = 0.99）。 |
| [A Meta-Analysis of Ten Learning Techniques](notes/papers/2021-ten-learning-techniques-meta.md) | 論文 | 2021 | T3 | 中 | 把 Dunlosky 等人（2013）評過的 10 種讀書技巧做成後設分析：**分散練習**（d = 0.85）和**練習測驗**（d = 0.74）效果最大，重讀、畫線、摘要最小（約 0.44–0.47）。 |
| [Automated Educational Question Generation at Different Bloom's Skill Levels using Large Language Models: Strategies and Evaluation](notes/papers/2024-bloom-question-generation.md) | 論文 | 2024 | T3、T8 | 高 | 讓 5 個 LLM 依 Bloom 分級幫研究所資料科學課出題：整體 78% 的題目被兩位專家評為高品質，但其中只有約 66% 真的符合指定的認知層級；7B 模型的層級符合率約 60%。 |
| [Unifying AI Tutor Evaluation: An Evaluation Taxonomy for Pedagogical Ability Assessment of LLM-Powered AI Tutors](notes/papers/2025-unifying-ai-tutor-eval.md) | 論文 | 2025 | T8、T3 | 高 | 提出評估 AI 家教「教得好不好」的 8 個維度，並用 192 段學生犯錯的數學對話測 7 個 LLM：GPT-4 很會答題，但約一半的時候直接洩漏答案，是「好的問答系統、普通的家教」；而用 Prometheus2 和 Llama-3.1-8B 當評審，和人類判斷的相關多半是負的，不可靠。 |
| [Anki 官方手冊：複習流程、作答按鈕、Leech、FSRS 期望記憶率、公式](notes/web/2026-anki-manual-review.md) | 文件 | 2026 | T7、T3 | 高 | Anki 的複習介面成熟且文件完整：先看題目、自己想、再翻答案，用 Again／Hard／Good／Easy 四個按鈕自評；一直忘記的卡片自動標成 **leech**。 |
| [ReAct: Synergizing Reasoning and Acting in Language Models](notes/papers/2023-react.md) | 論文 | 2023 | T4、T5 | 中 | 讓模型交替產生「想法」（reasoning trace）和「動作」（呼叫工具），用工具結果修正推理。 |
| [Small LLMs Are Weak Tool Learners: A Multi-LLM Agent（α-UMi）](notes/papers/2024-small-llms-weak-tool-learners.md) | 論文 | 2024 | T5、T4 | 中 | 一個小模型同時負責「規劃、呼叫工具、寫最終回答」會顧此失彼；把三件事拆給三個各自微調的小模型（planner、caller、summarizer），7B 就能在 ToolBench 上贏過單一 13B，部分指標接近 GPT-4。 |
| [TinyAgent: Function Calling at the Edge](notes/papers/2024-tinyagent.md) | 論文 | 2024 | T5、T4 | 高 | Berkeley 在 MacBook 上做了完全本地的 Siri 式助理：把小模型專門微調成「產生函式呼叫計畫」，再用一個小分類器只挑需要的工具放進提示，1.1B 和 7B 都超過 GPT-4-Turbo 的成功率。 |
| [Ollama 官方文件：ollama launch 與現成 agent 外殼整合、上下文長度](notes/web/2026-ollama-launch-integrations.md) | 文件 | 2026 | T4、T5 | 中 | `ollama launch` 能一鍵把現成的 agent 外殼（Claude Code、Codex、OpenCode、Qwen Code、Hermes Agent 等）接到本機模型，但官方對這類外殼一律建議至少 64k 的上下文，而這台 32 GB Mac 的預設只有 32k；外殼本身也是為寫程式設計的。 |
| [Ollama 官方文件：工具呼叫、結構化輸出、思考模式（含本機 qwen3.5:9b 設定）](notes/web/2026-ollama-tool-calling-structured-outputs.md) | 文件 | 2026 | T5、T4 | 高 | Ollama 原生支援工具呼叫（單次、平行、多輪 agent 迴圈）、用 `format` 參數強制 JSON schema 的結構化輸出，以及可開關的思考模式。 |
| [Ollama 官方文件：雲端功能、web search 與離線使用（加本機檢查）](notes/web/2026-ollama-cloud-offline.md) | 文件 | 2026 | T7、T4 | 高 | Ollama 在本機推論不需要網路，但**雲端模型和 web search 預設是開著的**；官方提供 `OLLAMA_NO_CLOUD=1` 或 `server.json` 一個設定就能關掉。 |
| [Qwen-Agent（Qwen 官方 agent 框架）與 Qwen 官方函式呼叫文件](notes/repos/QwenLM-Qwen-Agent.md) | 專案 | 2026 | T4、T5 | 中 | Qwen 官方的 agent 框架，模型卡推薦用它做 Qwen3.5 的 agent；它能接 Ollama 的 OpenAI 相容端點、有函式呼叫、MCP、RAG、Gradio 介面。 |
| [Qwen3.5-9B 官方模型卡（Hugging Face）](notes/web/2026-qwen35-9b-model-card.md) | 文件 | 2026 | T5、T4 | 高 | 官方說 Qwen3.5-9B「擅長工具呼叫」，自測 BFCL-V4 66.1、TAU2-Bench 79.1，並建議用 Qwen-Agent 或 Qwen Code 做 agent；但模型卡也建議思考模式要保留 128K 以上上下文，這和本機 Ollama 預設的 32k 有落差。 |
| [Large Language Models Cannot Self-Correct Reasoning Yet](notes/papers/2024-llms-cannot-self-correct.md) | 論文 | 2024 | T5 | 高 | 沒有外部回饋時，叫模型「檢查並修正自己的答案」（內在自我修正）不會變好，常常變差；過去說自我修正有效的研究，多半偷偷用了標準答案決定何時停止。 |
| [Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models](notes/papers/2024-let-me-speak-freely.md) | 論文 | 2024 | T5 | 高 | 強制模型輸出 JSON 等格式，會讓**推理題**變差，越嚴格的限制退步越多；但**分類題**反而可能變好。 |
| [The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models](notes/papers/2025-bfcl.md) | 論文 | 2025 | T5 | 中 | 工具呼叫的事實標準基準。 |
| [When is Deep Learning the Best Approach to Knowledge Tracing?](notes/papers/2020-knowledge-tracing-comparison.md) | 論文 | 2020 | T6 | 中 | 在 9 個真實資料集上比較三類「預測學生下一題會不會答對」的模型：資料中等或每人作答很多時，選對特徵的邏輯迴歸最好；資料很大或順序很重要時，深度模型 DKT 最好；經典的 BKT 落後。 |
| [QLoRA: Efficient Finetuning of Quantized LLMs](notes/papers/2023-qlora.md) | 論文 | 2023 | T6 | 中 | 先把模型壓成 4-bit 並凍結，只訓練外掛的小矩陣（LoRA），就能用一張 48 GB 的 GPU 微調 65B 模型，效果接近 16-bit 全參數微調。 |
| [Does Fine-Tuning LLMs on New Knowledge Encourage Hallucinations?](notes/papers/2024-new-knowledge-hallucination.md) | 論文 | 2024 | T6 | 中 | 用微調教模型「它原本不知道的事實」，模型學得很慢；一旦硬學會，反而更會編造，連沒訓練過的問題也受影響。 |
| [Ollama 官方文件：匯入模型、Modelfile、ollama create 量化](notes/web/2026-ollama-model-import.md) | 文件 | 2026 | T6 | 中 | 微調後的模型要回到 Ollama，目前官方文件只寫兩條路：匯入完整的 Safetensors 權重，或匯入 GGUF。 |
| [mlx-lm：在 Apple Silicon 上用 MLX 跑和微調 LLM（含 LORA.md）](notes/repos/ml-explore-mlx-lm.md) | 專案 | 2026 | T6 | 中 | Apple 官方的 MLX 套件 mlx-lm 可以在 Mac 上做 LoRA 和 QLoRA 微調，官方文件說 32 GB 的機器能微調 7B 模型。 |
| [Gradio 的離線行為：字型、使用分析、分享連結、公式（官方 repo 的文件與原始碼）](notes/web/2026-gradio-offline.md) | 文件 | 2026 | T7 | 中 | 新版 Gradio 的預設字型已經是內建檔案、公式用打包好的 KaTeX，看起來可以離線；但**使用分析預設開啟**，要設 `GRADIO_ANALYTICS_ENABLED=False`，自訂主題也不要用 `GoogleFont`。 |
| [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena](notes/papers/2023-llm-as-judge-mt-bench.md) | 論文 | 2023 | T8 | 中 | 最常被引用的「用模型當評審」研究：GPT-4 評審和人類專家的一致率（85%）可以達到人類彼此之間的水準（81%），但評審有位置偏誤、偏好冗長回答、可能偏好自己，而且會被題目附的錯誤答案誤導；給參考答案能大幅改善。 |
| [ARES: An Automated Evaluation Framework for Retrieval-Augmented Generation Systems](notes/papers/2024-ares-rag-eval.md) | 論文 | 2024 | T8 | 低 | 把 RAG 系統拆成三件事來評：檢索到的段落相不相關、答案有沒有忠於段落、答案有沒有回答問題；用小模型當評審，再用約 150 筆以上的人工標註，透過「預測驅動推論」（PPI）校正評審的誤差並給出信賴區間。 |
| [Position: Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints](notes/papers/2025-clt-small-evals.md) | 論文 | 2025 | T8 | 高 | 題目少於幾百題時，常見的「平均 ± 1.96 × 標準誤」誤差範圍太窄，會讓人以為結果很確定；小題組應該改用 Wilson 區間或簡單的貝氏方法，比較兩個模型時要利用「同一組題目」的配對結構。 |

## B 參考

| 來源 | 類型 | 年份 | 主題 | 適用度 | 一句話 |
|---|---|---|---|---|---|
| [AI-TA: Towards an Intelligent Question-Answer Teaching Assistant using Open-Source LLMs](notes/papers/2023-ai-ta-open-source-llms.md) | 論文 | 2023 | T1、T2、T6、T8 | 高 | 用開源的 LLaMA-2（7B、13B、70B）做課程問答助教，比較 RAG、微調和偏好訓練：**RAG 的效果最大，只做微調反而變差**；13B 加上全部方法，人工評分接近、但仍低於 GPT-4 加 RAG。 |
| [Towards an Efficient, Customizable, and Accessible AI Tutor](notes/papers/2025-offline-ai-tutor-rice.md) | 論文 | 2025 | T1、T2、T5 | 中 | 完全離線的「小模型 + 檢索」家教初步實驗：用生物課本建索引，給 SmolLM（1.35 億和 17 億參數）加上檢索段落後，選擇題正確率**不升反降**；作者認為太小的模型處理不了變長的上下文。 |
| [Alan: A Classroom Deployment of An Educational Chatbot That Cites Resources](notes/papers/2026-alan-cites-resources.md) | 論文 | 2026 | T1、T2、T7 | 中 | 多倫多大學的課程助教 Alan 只用老師核可的講義、實驗說明和錄影逐字稿回答，每個回答都附可點的出處。 |
| [Introducing Contextual Retrieval](notes/web/2024-contextual-retrieval.md) | 文章 | 2024 | T2 | 中 | 在每個切段前面加一兩句「這段在講什麼、出自哪裡」再建索引，並且關鍵字檢索和向量檢索一起用；廠商自測，前 20 個結果的漏找率可以降 49%，再加重排序可以降 67%。 |
| [Retrieval-Augmented Generation for Large Language Models: A Survey](notes/papers/2024-rag-survey.md) | 論文 | 2024 | T2、T6 | 中 | RAG（retrieval-augmented generation，先從資料庫找出相關段落、再交給模型作答）的綜述。 |
| [Smart Connections（Obsidian 外掛）](notes/repos/brianpetro-obsidian-smart-connections.md) | 專案 | 2026 | T7、T2 | 低 | v4 起核心外掛只做「找相關筆記」：內建本機嵌入模型，宣稱預設私密且離線；聊天功能拆到另一個外掛，而且**接 API 模型（包含本機 Ollama）的功能放在付費的 Smart Chat Pro**。 |
| [Towards Responsible Development of Generative AI for Education: An Evaluation-Driven Approach (LearnLM-Tutor)](notes/papers/2024-learnlm-tutor-eval.md) | 論文 | 2024 | T8、T3 | 中 | Google 團隊把 Gemini 1.0 微調成 LearnLM-Tutor，並設計 7 種教學評估：有人工也有自動、有單輪也有多輪、有學生視角也有老師視角。 |
| [Obsidian Spaced Repetition 外掛](notes/repos/st3v3nmw-obsidian-spaced-repetition.md) | 專案 | 2026 | T7、T3 | 中 | 在 Obsidian 筆記裡直接寫閃卡（例如 `問題::答案`，或把 `==螢光==` 當挖空），在 Obsidian 內複習；1.15.0 起可以選 FSRS。 |
| [py-fsrs：FSRS 間隔重複排程的 Python 實作（只看怎麼存使用者狀態）](notes/repos/open-spaced-repetition-py-fsrs.md) | 專案 | 2026 | T6、T3 | 高 | FSRS（Free Spaced Repetition Scheduler，預測「什麼時候快忘了」來排下一次複習的演算法）把每張卡片的狀態壓成幾個數字，另外保留每次作答的紀錄；紀錄夠多時，可以用紀錄重新擬合參數。 |
| [Building effective agents（Anthropic 工程文章）](notes/web/2024-anthropic-building-effective-agents.md) | 文章 | 2024 | T4、T5 | 高 | 把「agentic 系統」分成兩類：**workflow**（LLM 和工具照預先寫好的程式路徑走）和 **agent**（LLM 自己決定流程和要用哪些工具）。 |
| [Small Language Models are the Future of Agentic AI](notes/papers/2025-slm-future-agentic.md) | 論文 | 2025 | T5、T4 | 高 | NVIDIA 的立場論文：agent 裡大多數模型呼叫是「重複、範圍窄、不需要聊天」的子任務，小模型（約 10B 以下）已經夠用、更合適也更便宜；需要通用對話時才少量呼叫大模型。 |
| [Copilot for Obsidian](notes/repos/logancyang-obsidian-copilot.md) | 專案 | 2026 | T7、T4 | 中 | README 自稱是下載量最高的 Obsidian AI 外掛，現在已經變成「在 Obsidian 裡跑 agent」的平台（後端可以接 OpenCode、Claude Code、Codex 等）。 |
| [Harness²: Recursive Agent Harnessing for an Open World](notes/repos/google-research-harness2.md) | 專案 | 2026 | T4、T5 | 中 | 自動改良「agent 外殼」（harness）的研究框架：在沒看過的任務上提出外殼修改、在同一題上試跑比較，再組合出更好的外殼。 |

## C 線索

目前沒有。C 級來源只用來找方向，記在各主題的 search-log，沒有寫成筆記。

## 內部資料

| 來源 | 類型 | 年份 | 主題 | 適用度 | 一句話 |
|---|---|---|---|---|---|
| [media-note 筆記格式（reading-v3）與查證規範](notes/internal/media-note.md) | 內部 | 2026 | T2、T3、T7 | 高 | 用 media-note 產生的課程筆記有固定的結構，AI TA 可以直接拿這個結構來切段、引用講義頁和出題；回答也可以沿用同一套寫法。 |
| [期中準備時用 Ollama App 的基準紀錄](notes/internal/ollama-app-baseline.md) | 內部 | 2026 | T2、T7、T8 | 高 | 沒做任何調整的 qwen3.5:9b 回答了 16 個期中課程問題。 |
| [本機實驗：qwen3.5:9b 的工具呼叫、工具數量、長系統提示與結構化輸出](notes/internal/2026-local-qwen35-tool-calling.md) | 文件 | 2026 | T5、T4 | 高 | 在「單一步驟、單一領域」的工具決定上，qwen3.5:9b 選工具、填參數幾乎都對，工具從 3 個加到 30 個、甚至套上 Codex 的系統提示，簡單情況下也沒變差；主要問題是**偶爾不呼叫工具卻說「已記錄」**，以及**長提示的冷啟動預填很慢**（4.6k token 要 17 秒、29k token 要 126 秒）。 |
