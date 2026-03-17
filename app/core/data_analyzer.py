"""
数据分析引擎：执行具体的数据分析操作
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import uuid

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class DataAnalyzer:
    """数据分析器"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化数据分析器

        Args:
            df: 要分析的数据DataFrame
        """
        self.df = df.copy()
        self.original_df = df.copy()
        logger.info(f"数据分析器初始化完成，数据规模: {len(df)}行 x {len(df.columns)}列")

    def execute_instruction(self, instruction: Dict) -> Dict:
        """
        执行分析指令

        Args:
            instruction: 分析指令，格式如 {"action": "filter", ...}

        Returns:
            执行结果
        """
        action = instruction.get("action")
        logger.info(f"执行分析指令: {action}")

        if action == "filter":
            return self._filter_data(instruction)
        elif action == "aggregate":
            return self._aggregate_data(instruction)
        elif action == "summary":
            return self._get_summary()
        elif action == "chart":
            return self._create_chart(instruction)
        else:
            return {
                "success": False,
                "error": f"未知指令: {action}"
            }

    def _filter_data(self, instruction: Dict) -> Dict:
        """
        筛选数据

        Args:
            instruction: 筛选指令，包含 column, operator, value
        """
        column = instruction.get("column")
        operator = instruction.get("operator")
        value = instruction.get("value")

        logger.info(f"筛选数据: {column} {operator} {value}")

        try:
            # 根据运算符构建筛选条件
            if operator == ">":
                filtered_df = self.df[self.df[column] > value]
            elif operator == "<":
                filtered_df = self.df[self.df[column] < value]
            elif operator == ">=":
                filtered_df = self.df[self.df[column] >= value]
            elif operator == "<=":
                filtered_df = self.df[self.df[column] <= value]
            elif operator == "==":
                filtered_df = self.df[self.df[column] == value]
            elif operator == "!=":
                filtered_df = self.df[self.df[column] != value]
            else:
                return {"success": False, "error": f"不支持的运算符: {operator}"}

            result = {
                "success": True,
                "action": "filter",
                "original_count": len(self.df),
                "filtered_count": len(filtered_df),
                "condition": f"{column} {operator} {value}",
                "data": filtered_df.head(10).to_dict('records'),
                "columns": list(filtered_df.columns)
            }

            logger.info(f"筛选完成，得到 {len(filtered_df)} 行")
            return result

        except Exception as e:
            logger.error(f"筛选失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _aggregate_data(self, instruction: Dict) -> Dict:
        """
        数据聚合计算

        Args:
            instruction: 聚合指令，包含 group_by, agg_column, agg_func
        """
        group_by = instruction.get("group_by", [])
        agg_column = instruction.get("agg_column")
        agg_func = instruction.get("agg_func")

        logger.info(f"聚合数据: 按 {group_by} 分组，计算 {agg_column} 的 {agg_func}")

        try:
            # 分组聚合
            if group_by:
                grouped = self.df.groupby(group_by)[agg_column].agg(agg_func).reset_index()
                result_data = grouped.to_dict('records')
            else:
                # 整体聚合
                if agg_func == "count":
                    result_value = len(self.df)
                else:
                    result_value = getattr(self.df[agg_column], agg_func)()
                result_data = [{f"{agg_func}_{agg_column}": result_value}]

            result = {
                "success": True,
                "action": "aggregate",
                "group_by": group_by,
                "agg_column": agg_column,
                "agg_func": agg_func,
                "result": result_data
            }

            logger.info(f"聚合完成，得到 {len(result_data)} 条结果")
            return result

        except Exception as e:
            logger.error(f"聚合失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _get_summary(self) -> Dict:
        """
        获取数据概要信息
        """
        logger.info("生成数据概要")

        try:
            summary = {
                "success": True,
                "action": "summary",
                "basic_info": {
                    "rows": len(self.df),
                    "columns": len(self.df.columns),
                    "column_names": list(self.df.columns)
                },
                "column_stats": []
            }

            # 遍历每一列，生成统计信息
            for col in self.df.columns:
                col_info = {
                    "name": col,
                    "type": str(self.df[col].dtype),
                    "missing": int(self.df[col].isnull().sum()),
                    "missing_percentage": round(float(self.df[col].isnull().sum() / len(self.df) * 100), 2)
                }

                # 数值列统计
                if pd.api.types.is_numeric_dtype(self.df[col]):
                    col_info.update({
                        "min": float(self.df[col].min()) if not pd.isna(self.df[col].min()) else None,
                        "max": float(self.df[col].max()) if not pd.isna(self.df[col].max()) else None,
                        "mean": float(self.df[col].mean()) if not pd.isna(self.df[col].mean()) else None,
                        "median": float(self.df[col].median()) if not pd.isna(self.df[col].median()) else None,
                        "std": float(self.df[col].std()) if not pd.isna(self.df[col].std()) else None
                    })
                else:
                    # 非数值列统计
                    col_info.update({
                        "unique_count": int(self.df[col].nunique()),
                        "top_values": self.df[col].value_counts().head(3).to_dict()
                    })

                summary["column_stats"].append(col_info)

            logger.info(f"数据概要生成完成")
            return summary

        except Exception as e:
            logger.error(f"生成概要失败: {str(e)}")
            return {"success": False, "error": str(e)}

    def _create_chart(self, instruction: Dict) -> Dict:
        """
        创建数据可视化图表

        Args:
            instruction: 图表指令，包含 chart_type, x_column, y_column, title
        """
        chart_type = instruction.get("chart_type")
        x_column = instruction.get("x_column")
        y_column = instruction.get("y_column")
        title = instruction.get("title", f"{chart_type}图表")

        logger.info(f"创建图表: {chart_type}, x={x_column}, y={y_column}")

        try:
            import matplotlib
            matplotlib.use('Agg')  # 使用非交互式后端
            import matplotlib.pyplot as plt

            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 创建图表
            plt.figure(figsize=(10, 6))

            if chart_type == "bar" or chart_type == "柱状图":
                # 柱状图 - 显示分类计数
                if x_column and x_column in self.df.columns:
                    data = self.df[x_column].value_counts()
                    data.plot(kind='bar')
                    plt.xlabel(x_column)
                    plt.ylabel("计数")
                    plt.title(title or f"{x_column}分布")
                else:
                    # 找第一个非数值列
                    for col in self.df.columns:
                        if not pd.api.types.is_numeric_dtype(self.df[col]):
                            data = self.df[col].value_counts()
                            data.plot(kind='bar')
                            plt.xlabel(col)
                            plt.ylabel("计数")
                            plt.title(title or f"{col}分布")
                            break

            elif chart_type == "histogram" or chart_type == "直方图":
                # 直方图 - 显示数值分布
                if x_column and x_column in self.df.columns and pd.api.types.is_numeric_dtype(self.df[x_column]):
                    self.df[x_column].hist(bins=20)
                    plt.xlabel(x_column)
                    plt.ylabel("频数")
                    plt.title(title or f"{x_column}分布")
                else:
                    # 找第一个数值列
                    numeric_cols = self.df.select_dtypes(include=['number']).columns
                    if len(numeric_cols) > 0:
                        self.df[numeric_cols[0]].hist(bins=20)
                        plt.xlabel(numeric_cols[0])
                        plt.ylabel("频数")
                        plt.title(title or f"{numeric_cols[0]}分布")
                    else:
                        return {"success": False, "error": "没有数值列可绘制直方图"}

            elif chart_type == "pie" or chart_type == "饼图":
                # 饼图
                if x_column and x_column in self.df.columns:
                    data = self.df[x_column].value_counts().head(8)
                    data.plot(kind='pie', autopct='%1.1f%%')
                    plt.ylabel('')
                    plt.title(title or f"{x_column}占比")
                else:
                    # 找第一个非数值列
                    for col in self.df.columns:
                        if not pd.api.types.is_numeric_dtype(self.df[col]):
                            data = self.df[col].value_counts().head(8)
                            data.plot(kind='pie', autopct='%1.1f%%')
                            plt.ylabel('')
                            plt.title(title or f"{col}占比")
                            break

            plt.tight_layout()

            # 保存图表
            import uuid
            from pathlib import Path

            chart_filename = f"chart_{uuid.uuid4().hex[:8]}.png"
            chart_path = Path("static/plots") / chart_filename
            chart_path.parent.mkdir(parents=True, exist_ok=True)

            plt.savefig(chart_path, dpi=100, bbox_inches='tight')
            plt.close()

            result = {
                "success": True,
                "action": "chart",
                "chart_type": chart_type,
                "title": title,
                "chart_path": str(chart_path),
                "chart_url": f"/static/plots/{chart_filename}"
            }

            logger.info(f"图表创建成功: {chart_path}")
            return result

        except Exception as e:
            logger.error(f"创建图表失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}