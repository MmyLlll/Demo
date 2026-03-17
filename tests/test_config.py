# test_config.py
from app.config import config

def test_config():
    """测试配置是否正确加载"""
    print(f"DeepSeek API Key: {config.DEEPSEEK_API_KEY[:5]}...")  # 只显示前5位
    print(f"Model: {config.DEEPSEEK_MODEL}")
    print(f"Debug mode: {config.DEBUG}")
    print(f"Upload folder: {config.UPLOAD_FOLDER}")
    print(f"Max file size: {config.MAX_FILE_SIZE / 1024 / 1024} MB")

if __name__ == "__main__":
    test_config()