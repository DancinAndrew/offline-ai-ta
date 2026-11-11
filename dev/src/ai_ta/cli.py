"""Command line entry point: ``python -m ai_ta <command>``."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from . import config, evaluate, explain, index, ingest, learner, llm, practice
from .ingest import Chunk
from .retrieve import Retriever

console = Console()
MIN_QUIZ_SECTION_CHARS = 200  # sections shorter than this rarely support a real question


def cmd_index(args: argparse.Namespace) -> int:
    manifest = ingest.load_manifest()
    chunks = ingest.load_chunks(manifest)
    with index.connect() as conn:
        count = index.rebuild(conn, chunks)
    by_kind = Counter(c.chunking for c in chunks)
    files = len({c.file for c in chunks})
    console.print(f"indexed {count} chunks from {files} notes: {dict(by_kind)}")
    return 0


def cmd_embed(args: argparse.Namespace) -> int:
    models = config.EMBEDDING_MODELS if args.model == "all" else (args.model,)
    chunkings = ("heading", "fixed") if args.chunking == "all" else (args.chunking,)
    with index.connect() as conn:
        for model in models:
            for chunking in chunkings:
                added = index.embed_chunks(conn, model, chunking)
                console.print(f"{model} / {chunking}: embedded {added} new chunks")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    with index.connect() as conn:
        retriever = Retriever(conn, chunking=args.chunking, model=args.model)
        for rank, hit in enumerate(retriever.search(args.query, k=args.k, method=args.method), start=1):
            pages = "、".join(dict.fromkeys(link.label for link in hit.chunk.page_links))
            console.print(f"[bold]{rank}.[/bold] {hit.chunk.location}  [dim]({hit.score:.3f})[/dim]")
            console.print(f"   [dim]{hit.chunk.file}{'  ' + pages if pages else ''}[/dim]")
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    with index.connect() as conn:
        retriever = Retriever(conn, model=args.model)
        result = explain.answer(args.question, retriever, k=args.k)
    console.print(Markdown(result.answer))
    console.print("\n[bold]出處[/bold]")
    for line in explain.sources(result):
        console.print(f"  {line}")
    if not result.check.ok:
        console.print("[yellow]出處標記不完整，請對照筆記確認。[/yellow]")
    console.print(f"[dim]{result.total_seconds:.1f} 秒，{len(result.answer)} 字[/dim]")
    return 0


def _pick_point(retriever: Retriever, states: dict[str, learner.PointState], topic: str | None) -> Chunk:
    by_id = {c.chunk_id: c for c in retriever.chunks.values()}
    if topic:
        candidates = [h.chunk for h in retriever.search(topic, k=8)
                      if len(h.chunk.text) >= MIN_QUIZ_SECTION_CHARS]
        if not candidates:
            raise SystemExit(f"找不到和「{topic}」相關、內容夠長的筆記段落。")
        # Prefer the relevant section practiced least often.
        return min(candidates, key=lambda c: states[c.chunk_id].attempts if c.chunk_id in states else 0)
    for state in learner.due_points(states) + learner.weak_points(states):
        if state.knowledge_point in by_id:
            return by_id[state.knowledge_point]
    raise SystemExit("目前沒有到期或常錯的知識點，請用 --topic 指定要練習的主題。")


def _read_answer(quiz: practice.QuizItem) -> str:
    prompt = "你的答案（輸入「提示」看提示，「放棄」看答案）："
    answer = console.input(prompt).strip()
    if answer == "提示":
        console.print(f"[cyan]提示：{quiz.hint}[/cyan]")
        answer = console.input(prompt).strip()
    return answer


def cmd_quiz(args: argparse.Namespace) -> int:
    with index.connect() as conn:
        retriever = Retriever(conn, model=args.model)
        for n in range(1, args.n + 1):
            states = learner.derive_state(learner.load_events())
            chunk = _pick_point(retriever, states, args.topic)
            attempts = states[chunk.chunk_id].attempts if chunk.chunk_id in states else 0
            bloom = practice.bloom_for(attempts)
            quiz = practice.make_question(chunk, bloom)
            console.print(f"\n[bold]第 {n} 題（{quiz.bloom_level}）[/bold]  [dim]{chunk.location}[/dim]")
            console.print(Markdown(quiz.question))
            answer = _read_answer(quiz)
            result = practice.grade(chunk, quiz, answer)
            console.print(f"\n[bold]{result.label}[/bold]")
            for part in result.correct_parts:
                console.print(f"  [green]✓[/green] {part}")
            for part in result.wrong_parts:
                console.print(f"  [red]✗[/red] {part}")
            console.print(Markdown(result.feedback))
            console.print("[bold]參考要點[/bold]")
            for point in quiz.reference_points:
                console.print(f"  - {point}")
            pages = "、".join(dict.fromkeys(link.label for link in chunk.page_links))
            console.print(f"[dim]出處：{chunk.location}{'（' + pages + '）' if pages else ''}[/dim]")
            learner.record(learner.Event(chunk.chunk_id, chunk.location, quiz.bloom_level, quiz.question,
                                         answer, result.label))
            state = learner.derive_state(learner.load_events())[chunk.chunk_id]
            console.print(f"[dim]掌握度 {state.mastery:.0%}，下次複習 {state.due.astimezone():%m/%d %H:%M}[/dim]")
    return 0


def cmd_progress(args: argparse.Namespace) -> int:
    states = learner.derive_state(learner.load_events())
    if not states:
        console.print("還沒有練習紀錄。")
        return 0
    table = Table(title="知識點")
    for column in ("知識點", "練習次數", "掌握度", "下次複習"):
        table.add_column(column)
    weak = {s.knowledge_point for s in learner.weak_points(states)}
    for s in sorted(states.values(), key=lambda s: s.mastery):
        mark = " [red](常錯)[/red]" if s.knowledge_point in weak else ""
        table.add_row(s.location + mark, str(s.attempts), f"{s.mastery:.0%}", f"{s.due.astimezone():%m/%d %H:%M}")
    console.print(table)
    return 0


def cmd_eval_retrieval(args: argparse.Namespace) -> int:
    items = evaluate.load_items()
    scores = []
    with index.connect() as conn:
        for chunking in args.chunkings.split(","):
            scores.append(evaluate.score_retrieval(conn, items, chunking=chunking, method="keyword",
                                                   model=config.EMBEDDING_MODELS[0], k=args.k))
            for model in config.EMBEDDING_MODELS:
                for method in ("vector", "hybrid"):
                    try:
                        scores.append(evaluate.score_retrieval(conn, items, chunking=chunking, method=method,
                                                               model=model, k=args.k))
                    except LookupError as exc:
                        console.print(f"[yellow]skipped {model} / {chunking}: {exc}[/yellow]")
                        break
    table = Table(title=f"Retrieval on {len(items)} questions (top {args.k})")
    for column in ("chunking", "method", "embedding model", f"recall@{args.k}", "MRR", "missed"):
        table.add_column(column)
    for s in scores:
        model = "—" if s.method == "keyword" else s.model
        table.add_row(s.chunking, s.method, model, f"{s.recall_at_k:.2f}", f"{s.mrr:.2f}", " ".join(s.misses))
    console.print(table)
    out = evaluate.run_path("retrieval", ".json")
    out.write_text(json.dumps({"version": evaluate.git_version(), "k": args.k, "questions": len(items),
                               "scores": [s.__dict__ for s in scores]}, ensure_ascii=False, indent=2), encoding="utf-8")
    console.print(f"[dim]saved {out.relative_to(config.REPO_ROOT)}[/dim]")
    return 0


def cmd_eval_explain(args: argparse.Namespace) -> int:
    items = evaluate.load_items()
    by_id = {item["id"]: item for item in items}
    baseline_answers = evaluate.load_baseline_answers()
    out = evaluate.run_path("explain")
    with index.connect() as conn:
        retriever = Retriever(conn, chunking=args.chunking, model=args.model)
        # Load both models before timing anything; cold starts are reported separately.
        retriever.search("暖機", k=1)
        llm.chat([{"role": "user", "content": "請回覆「好」。"}], options={"num_predict": 5}, purpose="warmup")
        records = []
        for item in items:
            history = []
            chain, parent = [], item.get("follow_up_of")
            while parent:
                chain.insert(0, by_id[parent])
                parent = by_id[parent].get("follow_up_of")
            for earlier in chain:  # fixed prefix: the original turns as they happened (decision 0003)
                history += [{"role": "user", "content": earlier["question_as_asked"]},
                            {"role": "assistant", "content": baseline_answers.get(earlier["id"], "")}]
            result = explain.answer(evaluate.question_text(item), retriever, k=args.k, history=history,
                                    retrieval_query=evaluate.retrieval_query(item, by_id))
            gold = set(item["gold_sections"])
            record = {
                "id": item["id"], "type": item["type"], "answer": result.answer,
                "chars": len(result.answer), "total_seconds": round(result.total_seconds, 2),
                "retrieval_seconds": round(result.retrieval_seconds, 2),
                "generation_seconds": round(result.generation_seconds, 2),
                "prompt_tokens": result.prompt_tokens, "output_tokens": result.output_tokens,
                "retrieved": [h.chunk.chunk_id for h in result.hits],
                "retrieved_gold": [h.chunk.chunk_id in gold for h in result.hits],
                "cited": list(result.check.cited), "citations_ok": result.check.ok,
                "refused": result.check.refused, "retries": result.retries,
                "history_turns": len(chain),
            }
            records.append(record)
            console.print(f"{item['id']}: {record['total_seconds']:5.1f} s  {record['chars']:4d} 字  "
                          f"cited {record['cited']}  ok={record['citations_ok']}")
    meta = {"version": evaluate.git_version(), "model": config.GENERATION_MODEL, "embedding_model": args.model,
            "chunking": args.chunking, "k": args.k, "options": explain.OPTIONS}
    with out.open("w", encoding="utf-8") as f:
        f.write(json.dumps({"meta": meta}, ensure_ascii=False) + "\n")
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    seconds = [r["total_seconds"] for r in records]
    chars = [r["chars"] for r in records]
    base_seconds = [i["baseline"]["seconds"] for i in items]
    base_chars = [i["baseline"]["answer_chars"] for i in items]
    console.print(f"\nAI TA: median {statistics.median(seconds):.1f} s, {statistics.median(chars):.0f} 字; "
                  f"citations ok {sum(r['citations_ok'] for r in records)}/{len(records)}")
    console.print(f"Baseline: median {statistics.median(base_seconds):.1f} s, {statistics.median(base_chars):.0f} 字")
    console.print(f"[dim]saved {out.relative_to(config.REPO_ROOT)}[/dim]")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ai_ta", description="Offline AI TA for course review")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("index", help="cut the notes into chunks and build the keyword index").set_defaults(func=cmd_index)

    p = sub.add_parser("embed", help="compute embeddings for the indexed chunks")
    p.add_argument("--model", default=config.EMBEDDING_MODEL, help="model name, or 'all' for every candidate")
    p.add_argument("--chunking", default="heading", choices=["heading", "fixed", "all"])
    p.set_defaults(func=cmd_embed)

    p = sub.add_parser("search", help="search mode: list matching note sections without generation")
    p.add_argument("query")
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--method", default=config.RETRIEVAL_METHOD, choices=["hybrid", "vector", "keyword"])
    p.add_argument("--chunking", default="heading", choices=["heading", "fixed"])
    p.add_argument("--model", default=config.EMBEDDING_MODEL)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("ask", help="explanation mode: a short answer with citations to the notes")
    p.add_argument("question")
    p.add_argument("--k", type=int, default=4)
    p.add_argument("--model", default=config.EMBEDDING_MODEL, help="embedding model")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("quiz", help="practice mode: answer a question, then get graded against the notes")
    p.add_argument("--topic", help="what to practice; without it, due or weak points come first")
    p.add_argument("--n", type=int, default=1, help="number of questions")
    p.add_argument("--model", default=config.EMBEDDING_MODEL, help="embedding model")
    p.set_defaults(func=cmd_quiz)

    sub.add_parser("progress", help="mastery, review dates, and weak points").set_defaults(func=cmd_progress)

    p = sub.add_parser("eval-retrieval", help="compare embedding models and chunkings on the eval set")
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--chunkings", default="heading,fixed", help="comma-separated: heading, fixed")
    p.set_defaults(func=cmd_eval_retrieval)

    p = sub.add_parser("eval-explain", help="run the eval set through explanation mode and measure it")
    p.add_argument("--k", type=int, default=4)
    p.add_argument("--chunking", default="heading", choices=["heading", "fixed"])
    p.add_argument("--model", default=config.EMBEDDING_MODEL, help="embedding model")
    p.set_defaults(func=cmd_eval_explain)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
