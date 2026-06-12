"""
Milestone 5 — Gradio web interface for the Hunter CS Professor Guide.

Run with:
  python3 app.py
"""

import gradio as gr

from generate import ask

EXAMPLES = [
    "What do students say about the clarity of Professor Tong Yi's lectures?",
    "How responsive is Professor Mahdi Makki to student questions?",
    "What do students say about Professor Susan Epstein's grading rubrics?",
    "How much time per week does CSCI 13500 require?",
    "Does Professor Mahdi Makki's course connect to real-world industry work?",
]


def handle_query(question: str):
    if not question.strip():
        return "Please enter a question.", ""
    result = ask(question)
    sources_text = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources_text


with gr.Blocks(title="Hunter CS Professor Guide") as demo:
    gr.Markdown(
        "# Hunter College CS Professor Guide\n"
        "Ask questions about CS professors at Hunter College. "
        "Answers are grounded in student reviews and course documents only."
    )

    inp = gr.Textbox(
        label="Your question",
        placeholder="e.g. What do students say about Professor Tong Yi's lectures?",
        lines=2,
    )
    btn = gr.Button("Ask", variant="primary")

    answer_out = gr.Textbox(label="Answer", lines=8, show_copy_button=True)
    sources_out = gr.Textbox(label="Retrieved from", lines=4)

    gr.Examples(examples=EXAMPLES, inputs=inp)

    btn.click(handle_query, inputs=inp, outputs=[answer_out, sources_out])
    inp.submit(handle_query, inputs=inp, outputs=[answer_out, sources_out])

if __name__ == "__main__":
    demo.launch()
