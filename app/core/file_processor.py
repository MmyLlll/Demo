"""
文件处理模块：负责文件上传、验证和解析
"""
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple
import hashlib
from datetime import datetime

from app.utils.logger import setup_logger

# 创建日志记录器
logger = setup_logger(__name__)

class FileProcessor:
    """文件处理器"""

    def __init__(self):
        """初始化文件处理器"""
        self.supported_formats = {
            '.csv': 'CSV文件',
            '.xlsx': 'Excel文件',
            '.xls': 'Excel文件(旧版)'
        }
        logger.info(f"文件处理器初始化完成，支持格式: {list(self.supported_formats.keys())}")

    def validate_file(self, file_path: Path) -> Tuple[bool, str]:
        """
        验证文件有效性

        Args:
            file_path: 文件路径

        Returns:
            (是否有效, 提示信息)
        """
        logger.info(f"开始验证文件: {file_path}")

        # 1. 检查文件是否存在
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return False, "文件不存在"

        # 2. 检查文件大小（限制100MB）
        file_size = file_path.stat().st_size
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            logger.error(f"文件过大: {file_size} bytes")
            return False, f"文件过大，最大支持 {max_size/1024/1024}MB"

        # 3. 检查文件扩展名
        suffix = file_path.suffix.lower()
        if suffix not in self.supported_formats:
            logger.error(f"不支持的文件格式: {suffix}")
            return False, f"不支持的文件格式，支持: {list(self.supported_formats.keys())}"

        # 4. 检查文件是否为空
        if file_size == 0:
            logger.error("文件为空")
            return False, "文件为空"

        logger.info(f"文件验证通过: {file_path.name}, 大小: {file_size} bytes")
        return True, "文件验证通过"

    def read_csv(self, file_path: Path) -> pd.DataFrame:
        """
        读取CSV文件，自动检测编码

        Args:
            file_path: CSV文件路径

        Returns:
            DataFrame
        """
        logger.info(f"开始读取CSV文件: {file_path}")

        # 尝试不同的编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'latin1']

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"使用 {encoding} 编码读取成功，共 {len(df)} 行，{len(df.columns)} 列")
                return df
            except UnicodeDecodeError:
                logger.debug(f"{encoding} 编码失败，尝试下一个")
                continue
            except Exception as e:
                logger.error(f"读取CSV文件时发生错误: {str(e)}")
                raise

        # 所有编码都失败
        error_msg = f"无法读取CSV文件，尝试了以下编码: {encodings}"
        logger.error(error_msg)
        raise Exception(error_msg)

    def read_excel(self, file_path: Path) -> pd.DataFrame:
        """
        读取Excel文件

        Args:
            file_path: Excel文件路径

        Returns:
            DataFrame
        """
        logger.info(f"开始读取Excel文件: {file_path}")

        # 先检查文件是否存在
        if not file_path.exists():
            error_msg = f"Excel文件不存在: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            logger.info(f"Excel文件读取成功，共 {len(df)} 行，{len(df.columns)} 列")
            return df

        except Exception as e:
            logger.error(f"读取Excel文件失败: {str(e)}")
            raise Exception(f"读取Excel文件失败: {str(e)}")

    def read_file(self, file_path: Path) -> pd.DataFrame:
        """
        根据文件扩展名自动选择读取方法

        Args:
            file_path: 文件路径

        Returns:
            DataFrame
        """
        suffix = file_path.suffix.lower()
        logger.info(f"根据扩展名 {suffix} 选择读取方法")

        if suffix == '.csv':
            return self.read_csv(file_path)
        elif suffix in ['.xlsx', '.xls']:
            return self.read_excel(file_path)
        else:
            error_msg = f"不支持的文件格式: {suffix}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def generate_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成数据概要信息

        Args:
            df: 数据DataFrame

        Returns:
            包含数据概要的字典
        """
        logger.info("开始生成数据概要")

        summary = {
            "basic_info": {
                "rows": len(df),
                "columns": len(df.columns),
                "memory_usage": f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB",
                "duplicate_rows": df.duplicated().sum()
            },
            "columns": []
        }

        # 遍历每一列，收集信息
        for col in df.columns:
            col_info = {
                "name": col,
                "type": str(df[col].dtype),
                "missing": int(df[col].isnull().sum()),
                "missing_percentage": round(float(df[col].isnull().sum() / len(df) * 100), 2)
            }

            # 如果是数值列，添加统计信息
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info.update({
                    "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                    "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                    "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                    "median": float(df[col].median()) if not pd.isna(df[col].median()) else None
                })
            else:
                # 如果是文本列，添加唯一值信息
                unique_values = df[col].dropna().unique()[:5]
                col_info.update({
                    "unique_count": int(df[col].nunique()),
                    "sample_values": [str(v) for v in unique_values]
                })

            summary["columns"].append(col_info)

        logger.info(f"数据概要生成完成，共 {summary['basic_info']['columns']} 列")
        return summary