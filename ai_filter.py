from dataclasses import dataclass

@dataclass
class AiFilter:
    """AI过滤结果数据类"""
    result: bool
    message: str = ""