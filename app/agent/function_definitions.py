"""
函数定义：定义DeepSeek可调用的数据分析函数
"""

def get_function_definitions():
    """获取函数定义列表"""
    return [
        {
            "name": "filter_data",
            "description": "根据条件筛选数据",
            "parameters": {
                "type": "object",
                "properties": {
                    "column": {
                        "type": "string",
                        "description": "要筛选的列名"
                    },
                    "operator": {
                        "type": "string",
                        "enum": [">", "<", ">=", "<=", "==", "!="],
                        "description": "比较运算符"
                    },
                    "value": {
                        "type": ["number", "string"],
                        "description": "比较的值"
                    }
                },
                "required": ["column", "operator", "value"]
            }
        },
        {
            "name": "aggregate_data",
            "description": "数据聚合计算",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "分组字段列表"
                    },
                    "agg_column": {
                        "type": "string",
                        "description": "要聚合的列"
                    },
                    "agg_func": {
                        "type": "string",
                        "enum": ["sum", "mean", "count", "min", "max"],
                        "description": "聚合函数"
                    }
                },
                "required": ["group_by", "agg_column", "agg_func"]
            }
        }
    ]