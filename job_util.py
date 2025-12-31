import logging
import random
import yaml
import json
from datetime import datetime, timedelta
from typing import TypeVar, Type, List, Optional, Callable
from pathlib import Path
import threading
import time
import schedule
from concurrent.futures import ThreadPoolExecutor
from boss_config import BossConfig
from logger import log
from dataclasses import dataclass

@dataclass
class Job:
    """职位信息数据类"""
    job_name: str = ""
    salary: str = ""
    job_area: str = ""
    company_name: str = ""
    recruiter: str = ""
    job_info: str = ""
    
    def __str__(self) -> str:
        return f"公司: {self.company_name}, 职位: {self.job_name}, 薪资: {self.salary}, 招聘者: {self.recruiter}"


T = TypeVar('T')

class JobUtils:
    """职位工具类"""
    
    UNLIMITED_CODE = "0"
    
    @staticmethod
    def append_param(name: str, value: str) -> str:
        """添加URL参数"""
        if value and value != JobUtils.UNLIMITED_CODE:
            return f"&{name}={value}"
        return ""
    
    @staticmethod
    def append_list_param(name: str, values: List[str]) -> str:
        """添加URL列表参数"""
        if values and values and values[0] != JobUtils.UNLIMITED_CODE:
            return f"&{name}={','.join(values)}"
        return ""
    
    @staticmethod
    def get_config(clazz: Type[T]) -> T:
        """
        从YAML配置文件加载配置
        
        Args:
            clazz: 配置类类型
            
        Returns:
            配置类实例
        """
        try:
            config_file = Path("boss/config.yaml")
            if not config_file.exists():
                raise FileNotFoundError("无法找到 config.yaml 文件")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 获取类名并转换为配置键
            class_name = clazz.__name__.lower().replace('config', '')
            
            if class_name not in config_data:
                raise KeyError(f"在配置文件中找不到 {class_name} 配置")
            
            # 将字典转换为配置类实例
            config_dict = config_data[class_name]
            
            # 如果配置类有from_dict方法，使用它
            if hasattr(clazz, 'from_dict'):
                return clazz.from_dict(config_dict)
            else:
                # 否则直接创建实例
                return clazz(**config_dict)
                
        except Exception as e:
            log.error(f"加载配置文件失败: {e}")
            raise
    
    @staticmethod
    def run_scheduled(platform):
        """
        运行定时任务
        
        Args:
            platform: 平台枚举
        """
        platform_name = platform.value if hasattr(platform, 'value') else str(platform)
        
        # 这里需要根据实际的平台调度类来调整
        platform_actions = {
            'BOSS': lambda: None,  # 需要替换为实际的函数 BossScheduled.post_jobs()
            'JOB51': lambda: None,  # 需要替换为实际的函数 Job51Scheduled.post_jobs()
            'LIEPIN': lambda: None,  # 需要替换为实际的函数 LiepinScheduled.post_jobs()
            'ZHILIAN': lambda: None,  # 需要替换为实际的函数 ZhilianScheduled.post_jobs()
            'LAGOU': lambda: None,  # 需要替换为实际的函数 LagouScheduled.post_jobs()
        }
        
        if platform_name in platform_actions:
            # 立即执行一次
            platform_actions[platform_name]()
            
            # 安排定时任务
            JobUtils.schedule_task_at_time(platform_name, 10, 0, platform_actions[platform_name])
            
            if platform_name == 'BOSS':
                JobUtils.schedule_task_at_time(platform_name, 15, 0, platform_actions[platform_name])
        else:
            log.warning("未定义的平台任务：%s", platform_name)
    
    @staticmethod
    def format_duration(start_date: datetime, end_date: datetime) -> str:
        """
        计算并格式化时间间隔
        
        Args:
            start_date: 开始时间
            end_date: 结束时间
            
        Returns:
            格式化后的时间字符串，格式为 "H时M分S秒"
        """
        duration = end_date - start_date
        total_seconds = int(duration.total_seconds())
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return f"{hours}时{minutes}分{seconds}秒"
    
    @staticmethod
    def format_duration_seconds(duration_seconds: int) -> str:
        """
        将给定的秒数转换为格式化的时间字符串
        
        Args:
            duration_seconds: 持续时间（秒）
            
        Returns:
            格式化后的时间字符串，格式为 "H时M分S秒"
        """
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        
        return f"{hours}时{minutes}分{seconds}秒"
    
    @staticmethod
    def schedule_task_at_time(platform: str, hour: int, minute: int, task: Callable):
        """
        通用的任务调度方法
        
        Args:
            platform: 平台名称
            hour: 要设置的小时，0-23之间的整数
            minute: 要设置的分钟，0-59之间的整数
            task: 要执行的任务函数
        """
        delay_seconds = JobUtils.get_initial_delay(hour, minute)
        
        msg = f"【{platform}】距离下次任务投递还有：{JobUtils.format_duration_seconds(delay_seconds)}，执行时间：{hour:02d}:{minute:02d}"
        log.info(msg)
        
        # 发送消息（需要实现Bot类）
        # Bot.send_message(msg)
        
        # 安排定时任务，每24小时执行一次
        def scheduled_task():
            # 第一次执行
            task()
            # 然后每天执行
            while True:
                time.sleep(24 * 3600)  # 24小时
                task()
        
        # 在新线程中运行定时任务
        thread = threading.Thread(target=scheduled_task, daemon=True)
        thread.start()
    
    @staticmethod
    def get_initial_delay(target_hour: int, target_minute: int) -> int:
        """
        计算从当前时间到指定时间（小时:分钟）的延迟
        
        Args:
            target_hour: 目标执行的小时
            target_minute: 目标执行的分钟
            
        Returns:
            延迟的秒数
        """
        now = datetime.now()
        next_run = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # 如果当前时间已经过了今天的目标时间，则将任务安排在明天
        if now > next_run:
            next_run += timedelta(days=1)
        
        delay = (next_run - now).total_seconds()
        return int(delay)
    
    @staticmethod
    def get_random_number_in_range(min_val: int, max_val: int) -> int:
        """
        获取指定范围内的随机数
        
        Args:
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            范围内的随机整数
        """
        if min_val > max_val:
            raise ValueError("max must be greater than or equal to min")
        
        return random.randint(min_val, max_val)
    
    @staticmethod
    def schedule_task_advanced(platform: str, task: Callable, 
                             hour: int = None, minute: int = None,
                             interval_hours: int = 24):
        """
        高级任务调度方法
        
        Args:
            platform: 平台名称
            task: 要执行的任务函数
            hour: 执行小时（None表示立即执行）
            minute: 执行分钟（None表示0分）
            interval_hours: 执行间隔小时数
        """
        if hour is None:
            # 立即执行
            task()
            msg = f"【{platform}】任务立即执行完成"
        else:
            minute = minute or 0
            delay_seconds = JobUtils.get_initial_delay(hour, minute)
            
            msg = f"【{platform}】距离下次任务投递还有：{JobUtils.format_duration_seconds(delay_seconds)}，执行时间：{hour:02d}:{minute:02d}"
            
            def scheduled_task():
                time.sleep(delay_seconds)
                task()
                # 后续定时执行
                while True:
                    time.sleep(interval_hours * 3600)
                    task()
            
            thread = threading.Thread(target=scheduled_task, daemon=True)
            thread.start()
        
        log.info(msg)
        # Bot.send_message(msg)
    
    @staticmethod
    def safe_get(dictionary: dict, key: str, default=None):
        """安全获取字典值"""
        return dictionary.get(key, default)
    
    @staticmethod
    def parse_json_safe(json_str: str, default=None):
        """安全解析JSON字符串"""
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def main():
        """测试方法"""
        start_time = datetime.now()
        time.sleep(3)
        duration = JobUtils.format_duration(start_time, datetime.now())
        print(duration)


# 平台枚举（需要根据实际情况定义）
class Platform:
    BOSS = "BOSS"
    JOB51 = "JOB51"
    LIEPIN = "LIEPIN"
    ZHILIAN = "ZHILIAN"
    LAGOU = "LAGOU"
    
    @staticmethod
    def get_platform_name(platform):
        """获取平台名称"""
        return platform


# 使用schedule库的替代方案
class AdvancedScheduler:
    """高级调度器（使用schedule库）"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def schedule_daily_task(self, platform: str, task: Callable, hour: int, minute: int = 0):
        """安排每日任务"""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._run_task, platform, task)
        
        msg = f"【{platform}】已安排每日任务，执行时间：{hour:02d}:{minute:02d}"
        log.info(msg)
        # Bot.send_message(msg)
    
    def schedule_interval_task(self, platform: str, task: Callable, hours: int = 24):
        """安排间隔任务"""
        schedule.every(hours).hours.do(self._run_task, platform, task)
        
        msg = f"【{platform}】已安排间隔任务，每{hours}小时执行一次"
        log.info(msg)
        # Bot.send_message(msg)
    
    def _run_task(self, platform: str, task: Callable):
        """运行任务"""
        try:
            log.info(f"开始执行【{platform}】任务")
            task()
            log.info(f"【{platform}】任务执行完成")
        except Exception as e:
            log.error(f"执行【{platform}】任务时出错: {e}")
    
    def start(self):
        """启动调度器"""
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        log.info("高级调度器已启动")


# 使用示例
if __name__ == "__main__":
    # 测试时间格式化
    start = datetime.now()
    time.sleep(2)
    print(f"耗时: {JobUtils.format_duration(start, datetime.now())}")
    
    # 测试随机数
    print(f"随机数: {JobUtils.get_random_number_in_range(1, 10)}")
    
    # 测试URL参数构建
    print(f"参数: {JobUtils.append_param('city', '101010100')}")
    print(f"列表参数: {JobUtils.append_list_param('experience', ['101', '102'])}")
    
    # 测试初始延迟计算
    delay = JobUtils.get_initial_delay(14, 30)
    print(f"到14:30的延迟: {delay}秒 ({JobUtils.format_duration_seconds(delay)})")
    
    # 测试配置加载（需要config.yaml文件）
    try:
        # 假设有一个BossConfig类
        config = JobUtils.get_config(BossConfig)
        print(f"配置: {config}")
        pass
    except Exception as e:
        print(f"配置加载测试失败: {e}")
