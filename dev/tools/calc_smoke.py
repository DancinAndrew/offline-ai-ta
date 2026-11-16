"""Run made-up calculation questions through the explanation flow and print what happened.

These questions are not in any eval set and use none of its numbers (decision 0006). They check
whether the calculator recipes and the answer checks carry over to problems the notes do not solve
(dev/harness/EXPERIENCE.md, changes 10 and 11). The answers need Ollama; nothing is saved.

Usage (repo root):

    PYTHONPATH=dev/src ../.venv/bin/python dev/tools/calc_smoke.py
"""

from ai_ta import explain, index
from ai_ta.retrieve import Retriever

QUESTIONS = [
    "二元分類的混淆矩陣（列是預測、欄是真實）：預測正：真實正 30、真實負 10；預測負：真實正 5、真實負 55。"
    "求兩類的 precision 和 recall。",
    "垃圾信分類用兩個二元特徵：有連結、有附件，已知類別時兩特徵條件獨立。Spam：先驗 0.4、P(有連結|Spam)=0.8、"
    "P(有附件|Spam)=0.3；Ham：先驗 0.6、P(有連結|Ham)=0.2、P(有附件|Ham)=0.1。一封信沒有連結也沒有附件，算出兩個後驗機率。",
    "用兩個二元特徵預測客戶會不會流失：有客訴（是/否）、月費高（是/否），已知類別時兩特徵條件獨立。流失：先驗 0.3、"
    "P(客訴=是|流失)=0.6、P(月費高=是|流失)=0.7；留下：先驗 0.7、P(客訴=是|留下)=0.2、P(月費高=是|留下)=0.3。"
    "新客戶有客訴、月費不高，算出兩個後驗機率並預測類別。",
    "判斷一顆水果是不是熟的，用三個是／否特徵：會軟、有香味、表皮有斑點，已知類別時特徵條件獨立。熟：先驗 0.45、"
    "P(會軟|熟)=0.9、P(有香味|熟)=0.7、P(有斑點|熟)=0.4；不熟：先驗 0.55、P(會軟|不熟)=0.1、P(有香味|不熟)=0.3、"
    "P(有斑點|不熟)=0.6。一顆水果會軟、沒有香味、有斑點，算出兩類的後驗機率。",
    "用 KNN（K=3）分類新點 (3, 3)。訓練資料：(1, 2) 類 A、(4, 4) 類 B、(2, 5) 類 A、(5, 1) 類 B、(3, 4) 類 B。"
    "新點會被分到哪一類？",
    "三類的混淆矩陣（列是真實、欄是預測）：真實 X：預測 X 8、Y 1、Z 1；真實 Y：X 2、Y 5、Z 3；真實 Z：X 0、Y 2、Z 8。"
    "求 macro precision 和 weighted recall。",
]


def main() -> None:
    with index.connect() as conn:
        retriever = Retriever(conn)
        for question in QUESTIONS:
            result = explain.answer(question, retriever)
            calculation = result.calculation
            print("=" * 90)
            print("Q:", question[:40], "| route:", result.route.type if result.route else None,
                  f"| {result.total_seconds:.1f} s, {len(result.answer)} 字, retries={result.retries} "
                  f"{result.retry_reasons} unresolved={result.unresolved}")
            if calculation:
                print(f"calc {calculation.seconds:.1f} s, error={calculation.error}, partial={calculation.partial}")
                print("STEPS:", " || ".join(step.text() for step in calculation.steps if not step.literal))
            print("A:", result.answer.replace("\n", " "), flush=True)


if __name__ == "__main__":
    main()
