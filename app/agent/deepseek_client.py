"""
DeepSeek API客户端：封装API调用
"""
import openai
from typing import Dict, List, Any, Optional
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.utils.logger import setup_logger
from app.config import config

logger = setup_logger(__name__)

class DeepSeekClient:
    """DeepSeek API客户端"""

    def __init__(self):
        """初始化DeepSeek客户端"""
        self.client = openai.OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1",
            timeout=60.0
        )
        self.model = config.DEEPSEEK_MODEL
        logger.info(f"DeepSeek客户端初始化完成，使用模型: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.APIError, openai.APIConnectionError, openai.RateLimitError))
    )
    def chat_completion(self, messages: List[Dict]) -> Dict:
        """
        调用DeepSeek聊天补全API（带重试机制）

        Args:
            messages: 消息列表

        Returns:
            API响应
        """
        try:
            logger.info("发送请求到DeepSeek API")
            logger.debug(f"请求消息: {json.dumps(messages, ensure_ascii=False)}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            # 解析响应
            result = {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

            logger.info(f"DeepSeek响应成功，finish_reason: {result['finish_reason']}, tokens: {result['usage']['total_tokens']}")
            return result

        except openai.RateLimitError as e:
            logger.warning(f"速率限制，将重试: {str(e)}")
            raise
        except openai.APIError as e:
            logger.error(f"API错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            raise

    # 👇 从这里开始是新添加的方法
    def chat_with_functions(self, messages: List[Dict], functions: List[Dict] = None) -> Dict:
        """
        调用DeepSeek聊天补全API（支持函数调用）

        Args:
            messages: 消息列表
            functions: 函数定义列表

        Returns:
            API响应（可能包含函数调用）
        """
        try:
            logger.info("发送函数调用请求到DeepSeek API")

            params = {
                "model": self.model,
                "messages": messages
            }

            # DeepSeek 可能使用不同的参数名
            if functions:
                params["functions"] = functions
                params["function_call"] = "auto"

            response = self.client.chat.completions.create(**params)

            # 解析响应
            message = response.choices[0].message
            result = {
                "content": message.content,
                "role": message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

            # 检查响应内容是否包含函数调用（DeepSeek 可能以文本形式返回）
            if message.content and 'function' in message.content:
                try:
                    # 尝试从 JSON 中提取函数调用
                    import re
                    json_match = re.search(r'```json\n(.*?)\n```', message.content, re.DOTALL)
                    if json_match:
                        func_data = json.loads(json_match.group(1))
                        result["function_call"] = {
                            "name": func_data.get("function"),
                            "arguments": func_data.get("parameters", {})
                        }
                        logger.info(f"从文本中解析出函数调用: {result['function_call']['name']}")
                except Exception as e:
                    logger.warning(f"解析函数调用失败: {str(e)}")

            # 标准的 function_call 处理
            if hasattr(message, 'function_call') and message.function_call:
                result["function_call"] = {
                    "name": message.function_call.name,
                    "arguments": json.loads(message.function_call.arguments)
                }
                logger.info(f"检测到标准函数调用: {result['function_call']['name']}")

            return result

        except Exception as e:
            logger.error(f"函数调用失败: {str(e)}")
            raise

    def parse_analysis_intent(self, user_query: str, data_context: Dict) -> Dict:
        """
        解析用户的分析意图，返回结构化的分析指令
        """
        columns = data_context.get('columns', [])
        columns_str = ', '.join(columns)

        prompt = f"""你是一个数据分析助手。基于用户的问题和数据信息，返回一个结构化的分析指令。

    数据信息：
    - 列名：{columns_str}

    用户问题：{user_query}

    请分析用户意图，并以JSON格式返回以下结构之一：

    1. 如果是筛选数据：
    {{"action": "filter", "column": "列名", "operator": ">/</>=/<=/==/!=", "value": 值}}

    2. 如果是聚合计算：
    {{"action": "aggregate", "group_by": ["列名"], "agg_column": "列名", "agg_func": "sum/mean/count/min/max"}}

    3. 如果是数据概览：
    {{"action": "summary"}}

    4. 如果是绘制图表：
       - 柱状图：{{"action": "chart", "chart_type": "bar", "x_column": "列名", "title": "标题"}}
       - 直方图：{{"action": "chart", "chart_type": "histogram", "x_column": "列名", "title": "标题"}}
       - 饼图：{{"action": "chart", "chart_type": "pie", "x_column": "列名", "title": "标题"}}

    只返回JSON，不要有其他内容。"""

        response = self.chat_completion([
            {"role": "system", "content": "你是一个数据分析助手，只返回JSON格式的响应。"},
            {"role": "user", "content": prompt}
        ])

        try:
            # 提取JSON
            import re
            import json
            content = response['content']
            # 查找JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                logger.info(f"解析结果: {result}")
                return result
            else:
                logger.warning(f"未找到JSON: {content}")
                return {"action": "unknown"}
        except Exception as e:
            logger.error(f"解析失败: {str(e)}")
            return {"action": "unknown"}