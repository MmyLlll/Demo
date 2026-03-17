# test_logger.py
from app.utils.logger import setup_logger

# 创建日志记录器
logger = setup_logger(__name__)


def test_logger():
    """测试日志功能"""
    logger.debug("这是debug信息")
    logger.info("这是info信息")
    logger.warning("这是warning信息")
    logger.error("这是error信息")

    print("日志已写入控制台和logs/app.log文件")


if __name__ == "__main__":
    test_logger()