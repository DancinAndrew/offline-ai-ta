# dev

AI TA 的程式、harness 和評估。架構見 [docs/architecture.md](../docs/architecture.md)。

| 資料夾 | 內容 |
|---|---|
| `src/ai_ta/` | 程式本體 |
| `harness/` | 提示詞、護欄、各模式的技能說明，用純文字存，改動就是 diff |
| `eval/` | 評估題組與每次的結果，見 [eval/README.md](eval/README.md) |
| `tests/` | 單元測試 |

## 準備

- **Ollama**：先安裝，並下載模型：`qwen3.5:9b`、`bge-m3`、`qwen3-embedding:0.6b`、`embeddinggemma-2:270m`。
- **離線設定**：`~/.ollama/server.json` 寫入 `{"disable_ollama_cloud": true}`，然後重啟 Ollama。
- **Python 環境**：套件清單在 repo 根目錄的 [`requirements.txt`](../requirements.txt)（`fsrs`、`gradio` 6.x、`numpy`、`pydantic`、`requests`、`rich`）。
  - 我自己用上層資料夾的共用 uv 環境（`../.venv`），下面的指令都照這個寫。
  - 別人自己建環境：`python -m venv .venv && .venv/bin/pip install -r requirements.txt`，並把指令裡的 `../.venv/bin/python` 換成 `.venv/bin/python`。
  - 程式新增套件時，兩邊都要加：上層用 `uv add`，這裡改 `requirements.txt`。

以下指令都在 repo 根目錄執行。

## 指令

```bash
# 切段並建立關鍵字索引（課程筆記清單在 data/knowledge/sources.json）
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta index
# 計算向量（預設模型見 dev/src/ai_ta/config.py）
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta embed

# 搜尋模式：只列出相關段落，不生成
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta search "資訊增益是什麼"
# 解釋模式：短答，附出處
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta ask "Minimize FPR 等於 maximize TNR 還是 TPR？"
# 練習模式：先作答，再批改
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta quiz --topic "決策樹" --n 3
# 學習進度：掌握度、下次複習、常錯的知識點
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta progress
# 一段複習（終端機）：練習到期和常錯的知識點、錯題換方式重講、隨時提問；輸入「結束」離開
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta review
# 一段複習（本機網頁，只聽 127.0.0.1）：開 http://127.0.0.1:7860，或加 --open 自動開瀏覽器
PYTHONPATH=dev/src ../.venv/bin/python -m ai_ta web

# 測試
PYTHONPATH=dev/src ../.venv/bin/python -m unittest discover -s dev/tests
```

## 執行時產生、只留本機的資料

| 位置 | 內容 |
|---|---|
| `data/index/index.sqlite` | 段落、關鍵字索引、向量；可以重建 |
| `data/learner/events.jsonl` | 練習紀錄；掌握度和複習時間都從它重算 |
| `data/logs/llm-calls.jsonl` | 每次呼叫模型的輸入、輸出和耗時 |
