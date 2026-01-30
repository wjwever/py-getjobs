import logging
import logging.handlers
import sys
from pathlib import Path

# LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

class CustomFormatter(logging.Formatter):
    """自定义日志格式化器，使用带颜色的等宽字符替换日志级别"""
    
    def format(self, record):
        # 使用带颜色的等宽字符替换日志级别名称
        level_symbols = {
            'DEBUG': 'ℹ️',    # 蓝色圆圈，相对等宽
            'INFO': '✅',     # 绿色对勾，相对等宽
            'WARNING': '🟡️',  # 黄色圆圈，相对等宽
            'ERROR': '❌',    # 红色圆圈，相对等宽
            'CRITICAL': '💥'  # 骷髅头，相对等宽
        }
        
        # 将级别名称替换为符号
        record.levelname = level_symbols.get(record.levelname, record.levelname)
        
        return super().format(record)

logger = logging.getLogger("")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    fmt = CustomFormatter("%(asctime)s %(levelname)s %(filename)s:%(lineno)d: %(message)s")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    fh = logging.handlers.RotatingFileHandler(
        LOG_DIR / "app.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

# 常用别名，代码中直接使用 `from logger import log`
log = logger

if __name__ == "__main__":
    log.debug("这是一个调试信息")
    log.info("这是一个普通信息")
    log.warning("这是一个警告信息")
    log.error("这是一个错误信息")
    log.critical("这是一个严重错误信息")
