import gradio as gr

def test_fn(file):
    if file is None:
        return "没有文件"
    return f"收到文件: {file.name}"

with gr.Blocks() as demo:
    file_input = gr.File(label="上传文件")
    output = gr.Textbox()
    btn = gr.Button("测试")
    btn.click(test_fn, inputs=[file_input], outputs=[output])

demo.launch()