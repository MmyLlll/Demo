"""
数据分析引擎测试
"""
import pytest
import pandas as pd
import numpy as np
from app.core.data_analyzer import DataAnalyzer


class TestDataAnalyzer:
    """测试数据分析器"""

    @pytest.fixture
    def sample_df(self):
        """创建示例数据"""
        return pd.DataFrame({
            '姓名': ['张三', '李四', '王五', '赵六', '钱七'],
            '年龄': [25, 30, 35, 40, 45],
            '部门': ['IT', 'HR', 'IT', 'Finance', 'HR'],
            '工资': [5000, 6000, 7000, 8000, 9000]
        })

    @pytest.fixture
    def analyzer(self, sample_df):
        """创建分析器实例"""
        return DataAnalyzer(sample_df)

    def test_initialization(self, analyzer, sample_df):
        """测试初始化"""
        assert len(analyzer.df) == len(sample_df)
        assert len(analyzer.df.columns) == len(sample_df.columns)

    def test_filter_data_greater(self, analyzer):
        """测试大于筛选"""
        instruction = {
            "action": "filter",
            "column": "年龄",
            "operator": ">",
            "value": 35
        }

        result = analyzer.execute_instruction(instruction)

        assert result["success"] == True
        assert result["filtered_count"] == 2  # 40, 45
        assert result["condition"] == "年龄 > 35"

    def test_aggregate_by_group(self, analyzer):
        """测试分组聚合"""
        instruction = {
            "action": "aggregate",
            "group_by": ["部门"],
            "agg_column": "工资",
            "agg_func": "mean"
        }

        result = analyzer.execute_instruction(instruction)

        assert result["success"] == True
        assert result["action"] == "aggregate"
        assert len(result["result"]) == 3  # IT, HR, Finance 三个部门

        # 验证IT部门的平均工资
        it_result = next(r for r in result["result"] if r["部门"] == "IT")
        assert it_result["工资"] == 6000  # (5000+7000)/2

    def test_aggregate_overall(self, analyzer):
        """测试整体聚合"""
        instruction = {
            "action": "aggregate",
            "group_by": [],
            "agg_column": "工资",
            "agg_func": "mean"
        }

        result = analyzer.execute_instruction(instruction)

        assert result["success"] == True
        assert len(result["result"]) == 1
        assert "mean_工资" in result["result"][0]
        assert result["result"][0]["mean_工资"] == 7000  # (5000+6000+7000+8000+9000)/5

    def test_aggregate_count(self, analyzer):
        """测试计数聚合"""
        instruction = {
            "action": "aggregate",
            "group_by": ["部门"],
            "agg_column": "姓名",
            "agg_func": "count"
        }

        result = analyzer.execute_instruction(instruction)

        assert result["success"] == True
        # 验证各部门人数
        dept_counts = {r["部门"]: r["姓名"] for r in result["result"]}
        assert dept_counts["IT"] == 2
        assert dept_counts["HR"] == 2
        assert dept_counts["Finance"] == 1

    def test_get_summary(self, analyzer):
        """测试获取数据概要"""
        instruction = {"action": "summary"}

        result = analyzer.execute_instruction(instruction)

        assert result["success"] == True
        assert result["action"] == "summary"
        assert result["basic_info"]["rows"] == 5
        assert result["basic_info"]["columns"] == 4

        # 验证列统计信息
        assert len(result["column_stats"]) == 4

        # 验证年龄列（数值列）
        age_stats = next(s for s in result["column_stats"] if s["name"] == "年龄")
        assert "min" in age_stats
        assert age_stats["min"] == 25
        assert age_stats["max"] == 45
        assert age_stats["mean"] == 35

        # 验证部门列（非数值列）
        dept_stats = next(s for s in result["column_stats"] if s["name"] == "部门")
        assert "unique_count" in dept_stats
        assert dept_stats["unique_count"] == 3
        assert len(dept_stats["top_values"]) <= 3

    def test_create_bar_chart(self, analyzer):
        """测试创建柱状图"""
        instruction = {
            "action": "chart",
            "chart_type": "bar",
            "x_column": "部门",
            "title": "各部门人数分布"
        }

        result = analyzer.execute_instruction(instruction)

        assert result["success"] == True
        assert result["action"] == "chart"
        assert result["chart_type"] == "bar"
        assert "chart_path" in result
        assert "chart_url" in result

    def test_create_histogram(self, analyzer):
        """测试创建直方图"""
        instruction = {
            "action": "chart",
            "chart_type": "histogram",
            "x_column": "年龄",
            "title": "年龄分布直方图"
        }

        result = analyzer.execute_instruction(instruction)

        assert result["success"] == True
        assert result["chart_type"] == "histogram"