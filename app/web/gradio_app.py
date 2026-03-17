"""
Web界面：使用Gradio构建交互式应用
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

import gradio as gr
import pandas as pd
import json

from app.core.file_processor import FileProcessor
from app.core.data_analyzer import DataAnalyzer
from app.agent.deepseek_client import DeepSeekClient
from app.config import config
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class DataAnalysisGradioApp:
    """数据分析Gradio应用"""

    def __init__(self):
        """初始化应用"""
        self.file_processor = FileProcessor()
        self.deepseek_client = DeepSeekClient()
        self.current_df = None
        self.current_analyzer = None
        logger.info("Gradio应用初始化完成")

    def process_uploaded_file(self, file):
        """处理上传的文件"""
        if file is None:
            return None, "请上传文件", {}

        try:
            file_path = Path(file.name)
            logger.info(f"处理文件: {file_path}")

            # 读取文件
            self.current_df = self.file_processor.read_file(file_path)
            self.current_analyzer = DataAnalyzer(self.current_df)

            # 生成概要
            summary = self.file_processor.generate_summary(self.current_df)

            # 准备数据预览
            preview = self.current_df.head(10)

            # 准备数据上下文
            data_context = {
                "columns": list(self.current_df.columns),
                "rows": len(self.current_df),
                "summary": summary
            }

            status = f"✅ 文件上传成功！共 {len(self.current_df)} 行，{len(self.current_df.columns)} 列"
            logger.info(status)

            return preview, status, data_context

        except Exception as e:
            error_msg = f"❌ 文件处理失败: {str(e)}"
            logger.error(error_msg)
            return None, error_msg, {}

    def analyze_query(self, query, history, data_context):
        """分析用户查询"""
        if self.current_df is None:
            return history + [[query, "请先上传数据文件"]], None

        try:
            logger.info(f"用户查询: {query}")

            # 解析意图
            instruction = self.deepseek_client.parse_analysis_intent(query, data_context)
            logger.info(f"解析结果: {instruction}")

            # 执行分析
            result = self.current_analyzer.execute_instruction(instruction)

            # 生成回复
            if result["success"]:
                if result["action"] == "filter":
                    data_records = result.get('data', [])
                    if data_records:
                        import pandas as pd
                        df_result = pd.DataFrame(data_records)
                        reply = f"筛选完成，找到 {result['filtered_count']} 条记录：\n\n{df_result.to_string(index=False)}"
                    else:
                        reply = f"筛选完成，找到 {result['filtered_count']} 条记录"
                    return history + [[query, reply]], None

                elif result["action"] == "aggregate":
                    reply = f"聚合结果：\n{json.dumps(result['result'], ensure_ascii=False, indent=2)}"
                    return history + [[query, reply]], None

                elif result["action"] == "summary":
                    reply = f"数据概要：\n总行数：{result['basic_info']['rows']}"
                    return history + [[query, reply]], None

                elif result["action"] == "chart":
                    # 图表返回图片路径
                    chart_path = result.get('chart_path')
                    if chart_path and Path(chart_path).exists():
                        reply = f"📊 {result['title']}"
                        return history + [[query, reply]], chart_path
                    else:
                        reply = "图表生成失败"
                        return history + [[query, reply]], None
                else:
                    reply = f"分析完成"
                    return history + [[query, reply]], None
            else:
                reply = f"分析失败：{result.get('error', '未知错误')}"
                return history + [[query, reply]], None

        except Exception as e:
            error_msg = f"分析出错: {str(e)}"
            logger.error(error_msg)
            return history + [[query, error_msg]], None

    def launch(self):
        """启动应用"""
        with gr.Blocks(title="智能数据分析助手", theme="soft") as demo:
            gr.Markdown("# 📊 智能数据分析助手")

            # 状态存储
            data_context = gr.Variable(value={})

            with gr.Row():
                with gr.Column(scale=1):
                    file_input = gr.File(label="上传数据文件 (CSV/Excel)")
                    upload_btn = gr.Button("📤 上传", variant="primary")
                    status = gr.Textbox(label="状态", interactive=False)

                with gr.Column(scale=2):
                    data_preview = gr.Dataframe(label="数据预览", height=300)

            with gr.Row():
                chatbot = gr.Chatbot(label="对话历史", height=300)
                # 添加图片显示区域
                chart_output = gr.Image(label="图表显示", height=300)

            with gr.Row():
                msg = gr.Textbox(label="输入问题", placeholder="例如：筛选出年龄大于30岁的数据", scale=4)
                send_btn = gr.Button("发送", variant="primary", scale=1)
                clear_btn = gr.Button("清空对话")

            # 事件绑定
            upload_btn.click(
                fn=self.process_uploaded_file,
                inputs=file_input,
                outputs=[data_preview, status, data_context]
            )

            # 修改这里：使用两个输出
            def analyze_with_chart(query, history, context):
                new_history, chart_path = self.analyze_query(query, history, context)
                return new_history, chart_path

            send_btn.click(
                fn=analyze_with_chart,
                inputs=[msg, chatbot, data_context],
                outputs=[chatbot, chart_output]
            )

            msg.submit(
                fn=analyze_with_chart,
                inputs=[msg, chatbot, data_context],
                outputs=[chatbot, chart_output]
            )

            clear_btn.click(
                fn=lambda: (None, None),
                inputs=None,
                outputs=[chatbot, chart_output]
            )

        # 启动应用
        demo.launch(
            server_port=7862,
            share=False,
            debug=config.DEBUG
        )

if __name__ == "__main__":
    app = DataAnalysisGradioApp()
    app.launch()