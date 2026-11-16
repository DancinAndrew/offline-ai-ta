"""The review session on a local web page (Gradio), built to work offline (decision 0007, architecture §7).

Network features are off: analytics and the version check (GRADIO_ANALYTICS_ENABLED, set before Gradio
is imported), public share links, server-side rendering, run history, and the footer. The default theme's
fonts and KaTeX ship inside the package. The server listens on 127.0.0.1 only and serves files only from
the folders the notes' slide links point to.
"""

from __future__ import annotations

import os

os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

from urllib.parse import quote  # noqa: E402

import gradio as gr  # noqa: E402

from . import config, index, review  # noqa: E402
from .ingest import PageLink  # noqa: E402
from .retrieve import Retriever  # noqa: E402

LATEX = [{"left": "$$", "right": "$$", "display": True}, {"left": "$", "right": "$", "display": False}]
QUICK = ("開始", "下一題", "提示", "放棄", "進度")
FONTS = ["Source Sans Pro", "PingFang TC", "Noto Sans TC", "system-ui", "sans-serif"]
CSS = ".status { font-size: 0.9em; }"


def page_url(link: PageLink) -> str:
    """Opens the slide PDF at the cited page in the browser's own viewer."""
    path = (config.VAULT_ROOT / link.pdf).resolve()
    return f"/gradio_api/file={quote(str(path))}#page={link.page}"


def slide_folders(retriever: Retriever) -> list[str]:
    return sorted({str((config.VAULT_ROOT / link.pdf).resolve().parent)
                   for chunk in retriever.chunks.values() for link in chunk.page_links})


def build(retriever: Retriever, events=None) -> gr.Blocks:
    sessions: dict[str, review.ReviewSession] = {}

    def session_for(request: gr.Request) -> review.ReviewSession:
        key = request.session_hash or "local"
        if key not in sessions:
            kwargs = {"events": events} if events else {}
            sessions[key] = review.ReviewSession(retriever, link=page_url, **kwargs)
        return sessions[key]

    def start(request: gr.Request):
        session = session_for(request)
        return [{"role": "assistant", "content": session.opening().markdown}], session.status()

    def add_message(text: str, history: list):
        if not text.strip():
            return "", history
        return "", history + [{"role": "user", "content": text.strip()}]

    def respond(history: list, request: gr.Request):
        session = session_for(request)
        last = history[-1] if history else None
        if not last or last["role"] != "user":
            return history, session.status()
        text = last["content"] if isinstance(last["content"], str) else str(last["content"])
        replies = session.handle(text)
        history = history + [{"role": "assistant", "content": reply.markdown} for reply in replies]
        return history, session.status()

    with gr.Blocks(title="AI TA 複習") as demo:
        with gr.Row():
            with gr.Column(scale=4):
                chat = gr.Chatbot(latex_delimiters=LATEX, height=620, label="複習", group_consecutive_messages=False)
                with gr.Row():
                    box = gr.Textbox(placeholder="作答、提問，或說想練的主題（例如「我想練決策樹」）", show_label=False,
                                     scale=6, autofocus=True)
                    send = gr.Button("送出", variant="primary", scale=1)
                with gr.Row():
                    quick = [gr.Button(name, size="sm") for name in QUICK]
            with gr.Column(scale=1):
                status = gr.Markdown(elem_classes="status")

        demo.load(start, outputs=[chat, status])
        for trigger in (box.submit, send.click):
            trigger(add_message, [box, chat], [box, chat], queue=False).then(respond, chat, [chat, status])
        for button, name in zip(quick, QUICK):
            button.click(lambda history, name=name: history + [{"role": "user", "content": name}], chat, chat,
                         queue=False).then(respond, chat, [chat, status])
    # One request at a time: the session and the index are shared, and a double click waits its turn.
    demo.queue(default_concurrency_limit=1)
    return demo


def launch(port: int = 7860, open_browser: bool = False) -> None:
    conn = index.connect(check_same_thread=False)
    retriever = Retriever(conn)
    retriever._vectors()   # load the vectors now, so requests never read the index file
    demo = build(retriever)
    demo.launch(server_name="127.0.0.1", server_port=port, share=False, ssr_mode=False, inbrowser=open_browser,
                allowed_paths=slide_folders(retriever), footer_links=[], run_history=False,
                theme=gr.themes.Default(font=FONTS), css=CSS)
