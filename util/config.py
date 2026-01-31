"""
Boss直聘自动投递脚本配置模块
支持YAML配置加载、单例模式、类型验证和错误检查
"""

import os
import re
import yaml
from dataclasses import dataclass, field, fields
from typing import List, Optional, Any, Dict, Union
from pathlib import Path


class ConfigError(Exception):
    """配置错误基类"""
    pass


class ConfigValidationError(ConfigError):
    """配置验证错误"""
    pass


class ConfigFileError(ConfigError):
    """配置文件错误"""
    pass


def _to_snake(name: str) -> str:
    """将驼峰命名转换为蛇形命名"""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            # 只在当前大写字母前一个是小写字母，或后一个是小写字母时添加下划线
            # 例如: enableAI -> enable_ai (I前面是A，后面没有，不加)
            #       cityCode -> city_code (C前面是y，加)
            prev_lower = name[i - 1].islower()
            next_lower = i + 1 < len(name) and name[i + 1].islower()
            if prev_lower or next_lower:
                result.append('_')
        result.append(char.lower())
    return ''.join(result)


def _camel_to_snake_dict(data: Dict) -> Dict:
    """将字典的键从驼峰转换为蛇形"""
    if not isinstance(data, dict):
        return data
    return {_to_snake(k): v for k, v in data.items()}


@dataclass
class BossConfig:
    """Boss直聘配置"""
    debugger: bool = False
    say_hi: str = "您好,我有大模型、语音对话的相关经验,希望应聘这个岗位,期待可以与您进一步沟通,谢谢！"
    keywords: List[str] = field(default_factory=lambda: ["外企"])
    industry: List[str] = field(default_factory=lambda: ["不限"])
    city_code: List[str] = field(default_factory=lambda: ["杭州"])
    experience: List[str] = field(default_factory=lambda: ["5-10年"])
    job_type: str = "不限"
    salary: str = "20-50K"
    degree: List[str] = field(default_factory=lambda: ["不限"])
    scale: List[str] = field(default_factory=lambda: ["不限"])
    stage: List[str] = field(default_factory=lambda: ["不限"])
    expected_salary: List[int] = field(default_factory=lambda: [30])
    wait_time: int = 10
    filter_dead_hr: bool = True
    send_img_resume: bool = False
    dead_status: List[str] = field(default_factory=lambda: [
        "2周内活跃", "本月活跃", "2月内活跃", "半年前活跃"
    ])

    # 有效值枚举
    VALID_EXPERIENCES = ["应届毕业生", "1年以下", "1-3年", "3-5年", "5-10年", "10年以上"]
    VALID_JOB_TYPES = ["不限", "全职", "兼职"]
    VALID_SALARIES = ["3K以下", "3-5K", "5-10K", "10-20K", "20-50K", "50K以上"]
    VALID_DEGREES = ["不限", "初中及以下", "中专/中技", "高中", "大专", "本科", "硕士", "博士"]
    VALID_SCALES = ["不限", "0-20人", "20-99人", "100-499人", "500-999人", "1000-9999人", "10000人以上"]
    VALID_STAGES = ["不限", "未融资", "天使轮", "A轮", "B轮", "C轮", "D轮及以上", "已上市", "不需要融资"]
    VALID_CITY_CODES = ["全国", "北京", "上海", "杭州", "广州", "深圳", "成都", "天津"]

    def validate(self) -> None:
        """验证Boss配置"""
        errors = []

        # 验证列表字段
        for exp in self.experience:
            if exp not in self.VALID_EXPERIENCES:
                errors.append(f"无效的工作经验值: '{exp}'，有效值为: {self.VALID_EXPERIENCES}")

        for deg in self.degree:
            if deg not in self.VALID_DEGREES:
                errors.append(f"无效的学历值: '{deg}'，有效值为: {self.VALID_DEGREES}")

        for s in self.scale:
            if s not in self.VALID_SCALES:
                errors.append(f"无效的公司规模值: '{s}'，有效值为: {self.VALID_SCALES}")

        for st in self.stage:
            if st not in self.VALID_STAGES:
                errors.append(f"无效的融资阶段值: '{st}'，有效值为: {self.VALID_STAGES}")

        for city in self.city_code:
            if city not in self.VALID_CITY_CODES:
                errors.append(f"无效的城市代码: '{city}'，有效值为: {self.VALID_CITY_CODES}")

        # 验证单值字段
        if self.job_type not in self.VALID_JOB_TYPES:
            errors.append(f"无效的求职类型: '{self.job_type}'，有效值为: {self.VALID_JOB_TYPES}")

        if self.salary not in self.VALID_SALARIES:
            errors.append(f"无效的薪资范围: '{self.salary}'，有效值为: {self.VALID_SALARIES}")

        # 验证数值字段
        if not isinstance(self.wait_time, int) or self.wait_time < 0:
            errors.append("等待时间必须是正整数")

        if self.expected_salary and not all(isinstance(x, (int, float)) and x >= 0 for x in self.expected_salary):
            errors.append("期望薪资必须是正数")

        if not self.keywords:
            errors.append("搜索关键词(keywords)不能为空")

        if errors:
            raise ConfigValidationError("Boss配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors))


@dataclass
class AIConfig:
    """AI配置"""
    enable_ai: bool = False
    introduce: str = ""
    prompt: str = ""
    api_key: str = ""
    model: str = "deepseek-chat"
    url: str = "https://api.deepseek.com"
    resume_md: str = "config/resume.md"

    _URL_PATTERN = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)

    def validate(self) -> None:
        """验证AI配置"""
        if not self.enable_ai:
            return

        errors = []

        if not self.api_key and not os.environ.get("DEEPSEEK_API_KEY"):
            errors.append("AI功能已开启但未配置API密钥（请在配置文件中设置api_key或设置环境变量DEEPSEEK_API_KEY）")

        if not self.model:
            errors.append("AI模型名称不能为空")

        if not self.introduce:
            errors.append("AI功能已开启但自我介绍(introduce)为空")

        if self.url and not self._URL_PATTERN.match(self.url.strip()):
            errors.append(f"无效的API URL: '{self.url}'")

        if errors:
            raise ConfigValidationError("AI配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors))

    def get_api_key(self) -> str:
        """获取API密钥（优先配置文件，其次环境变量）"""
        return self.api_key or os.environ.get("DEEPSEEK_API_KEY", "")


@dataclass
class DBConfig:
    """数据库配置"""
    host: str = "localhost"
    user: str = "root"
    password: str = ""
    database: str = "py_getjobs"
    port: int = 3306

    def validate(self) -> None:
        """验证数据库配置"""
        errors = []

        if not self.host:
            errors.append("数据库主机地址不能为空")

        if not self.user:
            errors.append("数据库用户名不能为空")

        if not self.database:
            errors.append("数据库名称不能为空")

        if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
            errors.append(f"无效的端口号: {self.port}")

        if errors:
            raise ConfigValidationError("数据库配置验证失败:\n" + "\n".join(f"  - {e}" for e in errors))

    def get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class ConfigManager:
    """
    配置管理器（单例模式）
    
    使用示例:
        from config import get_config
        
        config = get_config("config.yaml")
        print(config.boss.keywords)
        print(config.ai.model)
    """
    _instance: Optional['ConfigManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def _ensure_initialized(self):
        """确保实例已初始化"""
        if not self._initialized:
            self._boss: Optional[BossConfig] = None
            self._ai: Optional[AIConfig] = None
            self._db: Optional[DBConfig] = None
            self._raw_config: Dict[str, Any] = {}
            self._config_path: Optional[str] = None
            self._initialized = True

    @classmethod
    def load(cls, config_path: Union[str, Path] = "config/config.yaml", validate: bool = True) -> 'ConfigManager':
        """
        加载YAML配置文件
        
        Args:
            config_path: 配置文件路径
            validate: 是否验证配置
            
        Returns:
            ConfigManager实例
        """
        instance = cls()
        instance._ensure_initialized()
        instance._config_path = str(config_path)
        
        path = Path(config_path)
        if not path.exists():
            raise ConfigFileError(f"配置文件不存在: {config_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigFileError(f"YAML解析错误: {e}")
        except Exception as e:
            raise ConfigFileError(f"读取配置文件失败: {e}")
        
        instance._raw_config = raw or {}
        
        # 解析各模块配置（将驼峰键名转换为蛇形）
        instance._boss = BossConfig(**cls._filter_fields(BossConfig, _camel_to_snake_dict(instance._raw_config.get('boss', {}))))
        instance._ai = AIConfig(**cls._filter_fields(AIConfig, _camel_to_snake_dict(instance._raw_config.get('ai', {}))))
        instance._db = DBConfig(**cls._filter_fields(DBConfig, instance._raw_config.get('db', {})))
        
        if validate:
            instance.validate()
        
        return instance

    @staticmethod
    def _filter_fields(dataclass_type, data: Dict) -> Dict:
        """过滤有效字段"""
        valid = {f.name for f in fields(dataclass_type)}
        return {k: v for k, v in data.items() if k in valid}

    def validate(self) -> None:
        """验证所有配置"""
        self._boss.validate()
        self._ai.validate()
        self._db.validate()

    def reload(self, validate: bool = True) -> 'ConfigManager':
        """重新加载配置"""
        if self._config_path:
            return self.load(self._config_path, validate)
        raise ConfigError("未设置配置文件路径，无法重新加载")

    @property
    def boss(self) -> BossConfig:
        if self._boss is None:
            raise ConfigError("配置未加载")
        return self._boss

    @property
    def ai(self) -> AIConfig:
        if self._ai is None:
            raise ConfigError("配置未加载")
        return self._ai

    @property
    def db(self) -> DBConfig:
        if self._db is None:
            raise ConfigError("配置未加载")
        return self._db

    def get_raw(self, key: str, default: Any = None) -> Any:
        """获取原始配置值，支持点号分隔（如 'boss.debugger'）"""
        value = self._raw_config
        for k in key.split('.'):
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            'boss': self._boss.__dict__ if self._boss else {},
            'ai': self._ai.__dict__ if self._ai else {},
            'db': self._db.__dict__ if self._db else {}
        }

    def __repr__(self) -> str:
        return f"ConfigManager(config_path='{self._config_path}')"


# 便捷函数
def get_config(config_path: Union[str, Path] = "config.yaml", validate: bool = True) -> ConfigManager:
    """获取配置管理器实例（单例）"""
    return ConfigManager.load(config_path, validate)


# 全局配置实例
config: Optional[ConfigManager] = None


def init_config(config_path: Union[str, Path] = "config/config.yaml", validate: bool = True) -> ConfigManager:
    """初始化全局配置"""
    global config
    config = ConfigManager.load(config_path, validate)
    return config


if __name__ == "__main__":
    # 测试YAML使用驼峰命名（与原始配置文件兼容）
    test_yaml = '''
boss:
  debugger: false
  sayHi: "您好，希望应聘这个岗位"
  keywords: ["Java", "Python", "AI"]
  cityCode: ["杭州", "上海"]
  experience: ["5-10年"]
  salary: "20-50K"
  waitTime: 5
  filterDeadHR: true

ai:
  enableAI: true
  introduce: "我有5年开发经验"
  model: "deepseek-chat"
  api_key: ""

db:
  host: "localhost"
  user: "root"
  password: "secret"
  database: "test_db"
'''
    
    test_path = Path("test_config.yaml")
    test_path.write_text(test_yaml, encoding='utf-8')
    
    import os
    os.environ["DEEPSEEK_API_KEY"] = "test-key"
    
    try:
        print("=" * 50)
        print("测试配置加载（YAML驼峰 → Python蛇形）")
        print("=" * 50)
        
        cfg = get_config(test_path)
        
        print(f"\nBoss配置:")
        print(f"  关键词: {cfg.boss.keywords}")
        print(f"  城市: {cfg.boss.city_code}")  # 蛇形变量名
        print(f"  薪资: {cfg.boss.salary}")
        print(f"  等待时间: {cfg.boss.wait_time}")  # 蛇形变量名
        print(f"  打招呼语: {cfg.boss.say_hi}")  # 蛇形变量名
        
        print(f"\nAI配置:")
        print(f"  启用AI: {cfg.ai.enable_ai}")  # 蛇形变量名
        print(f"  API密钥: {cfg.ai.get_api_key()[:10]}...")
        
        print(f"\n数据库配置:")
        print(f"  连接字符串: {cfg.db.get_connection_string()}")
        
        print(f"\n单例测试: {cfg is get_config(test_path)}")
        
        print("\n" + "=" * 50)
        print("所有测试通过!")
        print("=" * 50)
        
    finally:
        if test_path.exists():
            test_path.unlink()
