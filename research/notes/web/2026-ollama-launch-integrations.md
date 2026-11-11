---
title: "Ollama 官方文件：ollama launch 與現成 agent 外殼整合、上下文長度"
type: doc
tier: A
fit: 中
topics: [T4, T5]
year: 2026
venue: "docs.ollama.com/integrations 與 /context-length（2026-11-11 讀取）；本機 Ollama 0.40.10 的 `ollama launch --help`"
url: https://docs.ollama.com/integrations/index
self_reported: false
status: read
accessed: 2026-11-11
---
## 一句話

`ollama launch` 能一鍵把現成的 agent 外殼（Claude Code、Codex、OpenCode、Qwen Code、Hermes Agent 等）接到本機模型，但官方對這類外殼一律建議至少 64k 的上下文，而這台 32 GB Mac 的預設只有 32k；外殼本身也是為寫程式設計的。

## 他們怎麼做

- **支援清單**（本機 `ollama launch --help`，0.40.10）：claude（Claude Code）、chatgpt（ChatGPT／Codex App）、hermes（Hermes Agent）、openclaw、opencode、codex、hermes-desktop、copilot、omp、droid、dsh（DeepSeek Harness）、kimi、muse、pi、pool、cline、qwen（Qwen Code）、vscode。
- **`ollama launch` 做的事**：沒安裝就提示安裝（npm 或官方安裝腳本，需要網路），再把外殼的模型供應者設成本機 Ollama。`--config` 只設定不啟動；`--restore` 還原。Claude Code 走 Ollama 的 Anthropic 相容 API；OpenCode、Hermes 走 OpenAI 相容 API（`http://localhost:11434/v1`）；Codex 用 Responses API 的設定檔。
- **上下文長度要求**（各整合頁與 [Context length](https://docs.ollama.com/context-length)）：
  - Claude Code、Codex、OpenClaw：建議 64k 以上；OpenCode：「需要」64k 以上。
  - 通則：「web search、agent、寫程式工具這類需要大上下文的任務，至少設 64000 token。」
  - Ollama 依 VRAM 自動決定預設上下文：小於 24 GiB → 4k；24–48 GiB → 32k；48 GiB 以上 → 256k。設大會多用記憶體。
- **各外殼的定位**（官方頁面描述）：
  - Claude Code：讀程式碼、改檔、跑指令；能力包括子代理、web search、web fetch、視覺、思考。
  - OpenCode：終端機寫程式 agent。
  - Hermes Agent（Nous Research）：會自動建立技能、跨工作階段記憶，**預設內建 70 多個技能**，可接 Telegram、Discord 等訊息平台。
  - OpenClaw：把訊息服務（WhatsApp、Telegram 等）接到 agent 的閘道；第一次啟動會顯示「工具存取風險」的安全提醒。
  - DeepSeek Harness：開發者預覽版，設定可能隨版本改變。
- **離線相關**：各外殼的 web search 都要 `ollama signin`（走 Ollama 雲端）；本機模型本身可離線。Ollama 的雲端功能預設開啟、可用 `OLLAMA_NO_CLOUD=1` 關閉，見另一份筆記 [Ollama 雲端與離線](2026-ollama-cloud-offline.md)。
- **相容層的缺口**（[Anthropic compatibility](https://docs.ollama.com/api/anthropic-compatibility)）：Ollama 只支援 Anthropic Messages API 的子集；`tool_choice` 不支援，延遲載入的工具（deferred tools）和雲端 web search「不完全支援」。所以 Claude Code 接 Ollama 時，部分功能不會照原樣運作（推論自文件）。

## 證據

- 官方文件與本機 `--help`，只說明「能接哪些、建議怎麼設」，沒有任何外殼搭配 9B 模型的品質數字。
- **本機核對**（2026-11-11）：qwen3.5:9b 載入後 `ollama ps` 顯示 CONTEXT 32768，符合 24–48 GiB 這一級的預設；API 傳 `num_ctx: 65536` 後仍顯示 32768（見 [本機實驗](../internal/2026-local-qwen35-tool-calling.md)）。
- **外殼提示的分量**（我自己量，2026-11-11）：Codex 的基本指示 `codex-rs/protocol/src/prompts/base_instructions/default.md` 是 20,903 bytes，用 qwen3.5:9b 的 tokenizer 算是 4,589 token，**還沒算工具定義和 AGENTS.md**；冷啟動預填要 17 秒（本機實驗 E3）。

## 對 AI TA：可以借用／不適用

- **可以借用**：
  - 要快速做「現成外殼 + 9B」的對照組時，`ollama launch` 是最省事的入口（但會安裝東西，要先問使用者）。
  - 外殼的設計（技能按需載入、子代理、記憶檔）可以參考，對應 [harness2 的 8 個元件](../repos/google-research-harness2.md)。
- **不適用**：
  - 這些外殼都是為「寫程式、操作檔案、上網」設計的。AI TA 的主流程是複習，外殼的程式碼工具（bash、改檔、patch）對它是無關的選項，只會增加選錯工具的機會（推論；本機實驗 E2、E3b 有測工具變多的影響）。
  - 官方建議 64k 上下文，但本機預設 32k；加大上下文要多用記憶體，且每次冷啟動預填要數十秒（本機實驗）。
  - web search 等功能需要雲端，斷網時會失敗。

## 限制與疑點

- 我沒有實際執行 `ollama launch`（會安裝或改設定，研究規則禁止），所以沒量到各外殼「實際送給模型」的完整提示和工具數；上面只量了 Codex 的基本指示檔。
- 各外殼的授權（2026-11-11，GitHub）：Codex Apache-2.0、OpenCode MIT、Qwen Code Apache-2.0、Cline Apache-2.0、Hermes Agent MIT、OpenClaw MIT、DeepSeek Harness MIT；Claude Code 的 GitHub repo 沒有開源授權。
- 整合清單變動快（例如 Claude Desktop、NemoClaw 只出現在文件索引，沒出現在 `--help`）。
