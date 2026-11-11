# Offline AI TA

An offline AI teaching assistant for exam-style review of a university machine learning course. It runs a local 9B model (Qwen3.5-9B via [Ollama](https://ollama.com)) on a laptop. It answers from my own course notes with citations, generates and grades quizzes, and keeps track of what I get wrong.

[中文版](README.zh-TW.md)

> **Status:** first working version in the terminal. Search, explanation and practice modes run on the local models, and the first evaluation is in [`dev/eval/runs/`](dev/eval/runs/). Usage is in [`dev/README.md`](dev/README.md); the project overview is in the [proposal](reports/2026-11-11-proposal.md).

## Why

- **Works without internet.** I first tried a bare local model while studying for the midterm on a flight. The answers were readable but not good enough, and nothing had been tuned. This project builds on that experience.
- **Personalized.** It is grounded in my own lecture notes and quiz history, so it is not a generic chatbot.
- **Course requirement.** It is built for the Machine Learning course at National Central University (Fall 2026), where students build their own AI TA on a local model.

## Core hypothesis

On scoped review tasks with course materials available, a 9B local model with a well-designed harness (prompts, tools, memory, workflow) can approach the quality of frontier models.

To test it, the same question set is run on three setups:

1. The bare local model (baseline).
2. The AI TA: the same model with this project's harness.
3. A frontier model given the same materials (reference ceiling; used only for evaluation).

## Approach

1. **Research** how others build course AI tutors, ground answers in course material, run agents on small models, and evaluate tutors. → [`research/`](research/)
2. **Decide** the design based on the findings. → [`docs/decisions/`](docs/decisions/)
3. **Build** a minimal offline version first, then the agent and the interface. → `dev/`
4. **Evaluate and report.** → `reports/`

The step order and decision log are in [`docs/plan.md`](docs/plan.md).

## Repository layout

| Folder | Contents |
|---|---|
| `research/` | Source notes rated by evidence strength (A/B/C), search logs, synthesis (Traditional Chinese) |
| `docs/` | Plan, course requirements, design decisions (Traditional Chinese) |
| `dev/` | Code, harness (prompts, tool descriptions), interface, evaluation |
| `data/` | Runtime data manifests; course files are not redistributed |
| `reports/` | Write-ups for readers outside the project (English and Traditional Chinese) |

Not published: AI interaction logs, personal study data, paper PDFs, and course materials.

## License

[MIT](LICENSE)
