import gradio as gr

with gr.Blocks(title="Test") as demo:
    gr.Markdown("# Hello from CMMS")

demo.launch()
