# 判斷題型

讀使用者的訊息，判斷它屬於哪一種，以 JSON 回覆。

- `check-understanding`：使用者先說出自己的理解（一個或幾個說法），再問對不對，例如「所以 A 是 B？」「我這樣理解對嗎？」。把每個說法拆成 `claims`，一個說法一項，盡量用使用者的原話。
- `calculation`：要算出一個數字。把算式寫成 Python 運算式放在 `expression`，例如 `-(2/5)*log2(2/5) - (3/5)*log2(3/5)`；可以用 `log`、`log2`、`log10`、`sqrt`、`exp`。
- `comparison`：問兩個以上的東西差在哪。
- `formula`：請你解釋一個公式或其中的符號。
- `fact`：問一個有明確答案的事實。
- `concept`：其他問概念是什麼、為什麼的問題。

不是 `check-understanding` 時，`claims` 留空；不是 `calculation` 時，`expression` 留空字串。
