import gradio as gr
import pandas as pd
from pathlib import Path


def upload_file(file):
    if file is None:
        return "请上传文件", None

    try:
        df = pd.read_csv(file.name)
        preview = df.head(10)
        return f"成功上传 {len(df)} 行", preview
    except Exception as e:
        return f"错误: {str(e)}", None


with gr.Blocks() as demo:
    gr.Markdown("# 测试应用")

    with gr.Row():
        file_input = gr.File(label="上传CSV")
        status = gr.Textbox(label="状态")

    preview = gr.Dataframe(label="预览")

    file_input.change(upload_file, inputs=[file_input], outputs=[status, preview])

demo.launch()