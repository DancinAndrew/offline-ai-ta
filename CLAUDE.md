# CLAUDE.md

Guidance for AI coding tools working in this folder.

## What this is

A personal AI teaching assistant (AI TA) for the NCU Machine Learning course (Prof. Chia-Yu Lin, 2026 Fall). It is an offline, exam-style review assistant that runs a local model (qwen3.5:9b via Ollama), answers from the user's own course notes with citations, generates and grades quizzes, tracks weak points, and works as an agent. It is developed and evaluated on the midterm material; the course has no final exam.

Read first:

- `docs/plan.md`: goal, scope, folder rules, step order, decision log
- `research/README.md`: research protocol (topics, source tiers, note template, file ownership for parallel sessions)
- `docs/course-requirements.md`: course requirements and grading

Hard constraints:

- Local model only at runtime, and it must work fully offline.
- **Personalized** (course notes, the user's quiz history), not a bare foundation model.
- **AI interaction records are graded deliverables.** Do not delete or rewrite anything in `records/`.

## Workflow

- Work one step at a time in the order given in `docs/plan.md`. Report when a step is done and wait for the user before starting the next one.
- Do not schedule dates or estimate durations.

## Public repository

This folder is the public GitHub repo `DancinAndrew/offline-ai-ta`.

- Never commit `records/`, `data/learner/`, `data/index/`, `research/pdfs/`, `dev/eval/private/`, course materials (they stay in `../Week*/` and `../Midterm Review/`), or questions copied from course materials.
- Check `git status` before every commit.
- Commits use the user's global git identity (their Gmail), the same as their other public repos.

## Languages

- Internal docs and research notes: Traditional Chinese.
- External docs (`README.md`, `reports/`): English, plus a Traditional Chinese copy (`*.zh-TW.md`).
- `CLAUDE.md`: English.
- File and folder names: ASCII only (letters, digits, hyphens).

## Layout

- `research/`: how others build AI tutors (notes, search logs, synthesis). No code.
- `docs/`: internal design (plan, course requirements, requirements, architecture, `decisions/`).
- `dev/`: code, harness (prompts, tool descriptions, and skills as plain text), UI, eval. Its structure is set when development starts.
- `data/`: runtime data for the model: `knowledge/` (manifests pointing to course files, which are never copied here), `index/`, `learner/`.
- `reports/`: finished write-ups for readers outside the project.
- `records/`: AI interaction records (local only).

## Environment

Use the shared venv in the parent folder: `../.venv`, a uv project defined by `../pyproject.toml` + `../uv.lock` (Python 3.12). Do not create another environment or use `uv run --with ...` ad-hoc installs. Add packages with `uv add` from the parent folder so the lock file stays in sync. The public repo will need its own dependency list before others can run it.

```bash
../.venv/bin/python script.py
```

Machine: Apple M5, 32 GB RAM. Ollama 0.40.10 with `qwen3.5:9b` installed.
