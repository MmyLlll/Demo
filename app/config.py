"""
配置文件：管理所有环境变量和配置参数
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """基础配置类"""

    # DeepSeek API配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not DEEPSEEK_API_KEY:
        raise ValueError("请设置DEEPSEEK_API_KEY环境变量")

    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # 应用配置
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    PORT = int(os.getenv("PORT", 7860))

    # 文件上传配置
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

    # 确保上传目录存在
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


# 创建配置实例
config = Config()