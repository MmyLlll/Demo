"""
DeepSeek客户端测试
"""
import pytest
from app.agent.deepseek_client import DeepSeekClient

class TestDeepSeekClient:
    """测试DeepSeek客户端"""

    @pytest.fixture
    def client(self):
        """创建客户端实例"""
        return DeepSeekClient()

    def test_client_initialization(self, client):
        """测试客户端初始化"""
        assert client.model is not None
        assert client.client is not None

    def test_chat_completion_basic(self, client):
        """测试基本聊天功能"""
        messages = [
            {"role": "system", "content": "你是一个有用的助手"},
            {"role": "user", "content": "你好，请简单介绍一下自己"}
        ]

        response = client.chat_completion(messages)

        assert "content" in response
        assert "role" in response
        assert response["role"] == "assistant"
        assert response["finish_reason"] == "stop"
        assert "usage" in response
        assert "total_tokens" in response["usage"]

    def test_chat_completion_with_system_prompt(self, client):
        """测试带系统提示的聊天"""
        messages = [
            {"role": "system", "content": "你是一个Python专家，只回答Python相关的问题"},
            {"role": "user", "content": "Python中的列表推导式是什么？"}
        ]

        response = client.chat_completion(messages)

        assert response["content"] is not None
        assert "列表" in response["content"] or "list" in response["content"].lower()

    def test_function_calling(self, client):
        """测试函数调用功能"""
        from app.agent.function_definitions import get_function_definitions

        functions = get_function_definitions()

        messages = [
            {"role": "system", "content": """你是一个数据分析助手。你必须使用我提供的函数来完成用户请求。
    当用户需要筛选数据时，调用 filter_data 函数，参数包括 column（列名）、operator（运算符）和 value（值）。"""},
            {"role": "user", "content": "筛选出年龄大于30岁的所有数据"}
        ]

        response = client.chat_with_functions(messages, functions)

        # 如果还是没有函数调用，打印响应内容帮助调试
        if "function_call" not in response:
            print(f"\n响应内容: {response['content']}")

        assert "function_call" in response, "应该返回函数调用"
        assert response["function_call"]["name"] == "filter_data"

        # 验证参数
        args = response["function_call"]["arguments"]
        assert "column" in args
        assert "operator" in args
        assert "value" in args
        assert args["column"] == "age" or args["column"] == "年龄"
        assert args["operator"] == ">"
        assert args["value"] == 30

    def test_parse_filter_intent(self, client):
        """测试解析筛选意图"""
        data_context = {
            "columns": ["姓名", "年龄", "部门", "工资"]
        }

        result = client.parse_analysis_intent(
            "筛选出年龄大于30岁的所有数据",
            data_context
        )

        assert result["action"] == "filter"
        assert result["column"] in ["年龄", "age"]
        assert result["operator"] == ">"
        assert result["value"] == 30

    def test_parse_aggregate_intent(self, client):
        """测试解析聚合意图"""
        data_context = {
            "columns": ["姓名", "年龄", "部门", "工资"]
        }

        result = client.parse_analysis_intent(
            "计算每个部门的平均工资",
            data_context
        )

        assert result["action"] == "aggregate"
        assert "部门" in result["group_by"]
        assert result["agg_column"] in ["工资", "salary"]
        assert result["agg_func"] == "mean"