import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from boss_enum import BossEnum

from logger import log as logger


@dataclass
class BossConfig:
    """
    Boss直聘配置类
    """
    # 用于打招呼的语句
    say_hi: str = ""
    
    # 开发者模式
    debugger: bool = False
    
    # 搜索关键词列表
    keywords: List[str] = field(default_factory=list)
    
    # 城市编码
    city_code: List[str] = field(default_factory=list)
    
    # 自定义城市编码映射
    custom_city_code: Dict[str, str] = field(default_factory=dict)
    
    # 行业列表
    industry: List[str] = field(default_factory=list)
    
    # 工作经验要求
    experience: List[str] = field(default_factory=list)
    
    # 工作类型
    job_type: str = ""
    
    # 薪资范围
    salary: str = ""
    
    # 学历要求列表
    degree: List[str] = field(default_factory=list)
    
    # 公司规模列表
    scale: List[str] = field(default_factory=list)
    
    # 公司融资阶段列表
    stage: List[str] = field(default_factory=list)
    
    # 是否开放AI检测
    enable_ai: bool = False
    
    # 是否过滤不活跃hr
    filter_dead_hr: bool = False
    
    # 是否发送图片简历
    send_img_resume: bool = False
    
    # 目标薪资
    expected_salary: List[int] = field(default_factory=list)
    
    # 等待时间
    wait_time: str = ""
    
    # HR未上线状态
    dead_status: List[str] = field(default_factory=list)
    
    # 城市代码映射缓存
    _city_code_map: Dict[str, str] = field(default_factory=dict, init=False)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BossConfig':
        """从字典创建配置对象"""
        return cls(
            say_hi=config_dict.get("sayHi", ""),
            debugger=config_dict.get("debugger", False),
            keywords=config_dict.get("keywords", []),
            city_code=config_dict.get("cityCode", []),
            custom_city_code=config_dict.get("customCityCode", {}),
            industry=config_dict.get("industry", []),
            experience=config_dict.get("experience", []),
            job_type=config_dict.get("jobType", ""),
            salary=config_dict.get("salary", ""),
            degree=config_dict.get("degree", []),
            scale=config_dict.get("scale", []),
            stage=config_dict.get("stage", []),
            enable_ai=config_dict.get("enableAi", False),
            filter_dead_hr=config_dict.get("filterDeadHr", False),
            send_img_resume=config_dict.get("sendImgResume", False),
            expected_salary=config_dict.get("expectedSalary", []),
            wait_time=config_dict.get("waitTime", ""),
            dead_status=config_dict.get("deadStatus", [])
        )
    
    def _load_city_code_from_json(self, json_path: Optional[str] = None) -> None:
        """从JSON文件加载城市代码"""
        if self._city_code_map:
            return
        
        if json_path:
            json_file = Path(json_path)
        else:
            json_file = Path("boss/city-industry-code.json")
        if not json_file.exists():
            # 尝试其他可能的位置
            json_file = Path("src/main/java/boss/city-industry-code.json")
            if not json_file.exists():
                logger.error(f"城市代码JSON文件不存在: {json_file.absolute()}")
                return
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            city_list = data.get("city", [])
            for city in city_list:
                name = city.get("name", "")
                code_obj = city.get("code")
                code = str(code_obj) if code_obj is not None else ""
                if name and code:
                    self._city_code_map[name] = code
                    
            logger.info(f"成功加载 {len(self._city_code_map)} 个城市代码")
            
        except Exception as e:
            logger.error(f"加载城市代码失败: {e}")
    
    def _get_city_code_from_json(self, city_name: str) -> Optional[str]:
        """根据城市名称获取城市代码"""
        return self._city_code_map.get(city_name)
    
    def _convert_city_codes(self):
        """转换城市编码"""
        converted_city_codes = []
        
        for city in self.city_code:
            # 优先从自定义映射中获取
            if self.custom_city_code and city in self.custom_city_code:
                converted_city_codes.append(self.custom_city_code[city])
                continue
            
            # 尝试从枚举中获取（不限、全国）
            try:
                enum_city = BossEnum.CityCode.for_value(city)
                if enum_city != BossEnum.CityCode.NULL or city in ["不限", "全国"]:
                    converted_city_codes.append(enum_city.code)
                    continue
            except:
                pass
            
            # 从JSON文件中获取
            code_from_json = self._get_city_code_from_json(city)
            if code_from_json:
                converted_city_codes.append(code_from_json)
                continue
            
            # 如果都找不到，返回"不限"的代码
            logger.warning(f"未找到城市【{city}】的代码，使用默认值 0")
            converted_city_codes.append("0")
        
        logger.info(f"转换后的城市代码: {self.city_code} -> {converted_city_codes}")
        self.city_code = converted_city_codes
    
    def _convert_job_type(self):
        """转换工作类型"""
        if self.job_type:
            try:
                job_type_enum = BossEnum.JobType.for_value(self.job_type)
                self.job_type = job_type_enum.code
            except Exception as e:
                logger.warning(f"转换工作类型失败: {e}, 使用默认值 0")
                self.job_type = "0"
    
    def _convert_salary(self):
        """转换薪资范围"""
        if self.salary:
            try:
                salary_enum = BossEnum.Salary.for_value(self.salary)
                self.salary = salary_enum.code
            except Exception as e:
                logger.warning(f"转换薪资范围失败: {e}, 使用默认值")
                self.salary = "0"
    
    def _convert_experience(self):
        """转换工作经验要求"""
        converted_experience = []
        for value in self.experience:
            try:
                exp_enum = BossEnum.Experience.for_value(value)
                converted_experience.append(exp_enum.code)
            except Exception as e:
                logger.warning(f"转换工作经验失败: {value}, 跳过")
                continue
        self.experience = converted_experience
    
    def _convert_degree(self):
        """转换学历要求"""
        converted_degree = []
        for value in self.degree:
            try:
                degree_enum = BossEnum.Degree.for_value(value)
                converted_degree.append(degree_enum.code)
            except Exception as e:
                logger.warning(f"转换学历要求失败: {value}, 跳过")
                continue
        self.degree = converted_degree
    
    def _convert_scale(self):
        """转换公司规模"""
        converted_scale = []
        for value in self.scale:
            try:
                scale_enum = BossEnum.Scale.for_value(value)
                converted_scale.append(scale_enum.code)
            except Exception as e:
                logger.warning(f"转换公司规模失败: {value}, 跳过")
                continue
        self.scale = converted_scale
    
    def _convert_stage(self):
        """转换公司融资阶段"""
        converted_stage = []
        for value in self.stage:
            try:
                stage_enum = BossEnum.Financing.for_value(value)
                converted_stage.append(stage_enum.code)
            except Exception as e:
                logger.warning(f"转换融资阶段失败: {value}, 跳过")
                continue
        self.stage = converted_stage
    
    def _convert_industry(self):
        """转换行业"""
        converted_industry = []
        for value in self.industry:
            try:
                industry_enum = BossEnum.Industry.for_value(value)
                converted_industry.append(industry_enum.code)
            except Exception as e:
                logger.warning(f"转换行业失败: {value}, 跳过")
                continue
        self.industry = converted_industry
    
    def init(self) -> 'BossConfig':
        """初始化配置，转换所有枚举值为代码"""
        # 加载城市代码JSON数据
        self._load_city_code_from_json()
        
        # 转换各种配置项
        self._convert_job_type()
        self._convert_salary()
        self._convert_city_codes()
        self._convert_experience()
        self._convert_degree()
        self._convert_scale()
        self._convert_stage()
        self._convert_industry()
        
        logger.info("配置初始化完成")
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "say_hi": self.say_hi,
            "debugger": self.debugger,
            "keywords": self.keywords,
            "city_code": self.city_code,
            "custom_city_code": self.custom_city_code,
            "industry": self.industry,
            "experience": self.experience,
            "job_type": self.job_type,
            "salary": self.salary,
            "degree": self.degree,
            "scale": self.scale,
            "stage": self.stage,
            "enable_ai": self.enable_ai,
            "filter_dead_hr": self.filter_dead_hr,
            "send_img_resume": self.send_img_resume,
            "expected_salary": self.expected_salary,
            "wait_time": self.wait_time,
            "dead_status": self.dead_status
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"BossConfig(keywords={self.keywords}, city_code={self.city_code}, " \
               f"job_type={self.job_type}, salary={self.salary})"


# 工具函数
def load_config_from_yaml(file_path: str = "boss/config.yaml") -> BossConfig:
    """
    从YAML文件加载配置
    :param file_path: 配置文件路径
    :return: BossConfig对象
    """
    try:
        import yaml
    except ImportError:
        logger.error("缺少yaml模块，请安装 pyyaml 包以支持YAML配置文件")
        raise
    
    try:
        config_file = Path(file_path)
        if not config_file.exists():
            logger.error(f"配置文件不存在: {file_path}")
            # TODO 创建默认配置
            default_config = BossConfig()
            return default_config.init()
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        logger.info(f"成功加载YAML配置文件: {config_dict['boss']}")
        config = BossConfig.from_dict(config_dict["boss"])
        return config.init()
        
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        # 返回默认配置
        default_config = BossConfig()
        return default_config.init()

# def load_config_from_file(file_path: str = "boss/config.json") -> BossConfig:
#     """
#     从JSON文件加载配置
#     :param file_path: 配置文件路径
#     :return: BossConfig对象
#     """
#     try:
#         config_file = Path(file_path)
#         if not config_file.exists():
#             logger.error(f"配置文件不存在: {file_path}")
#             # 创建默认配置
#             default_config = BossConfig()
#             return default_config.init()
        
#         with open(config_file, 'r', encoding='utf-8') as f:
#             config_dict = json.load(f)
        
#         config = BossConfig.from_dict(config_dict)
#         return config.init()
        
#     except Exception as e:
#         logger.error(f"加载配置文件失败: {e}")
#         # 返回默认配置
#         default_config = BossConfig()
#         return default_config.init()


# 使用示例
if __name__ == "__main__":
    # 示例配置
    sample_config = {
        "say_hi": "您好，我对这个职位很感兴趣",
        "debugger": True,
        "keywords": ["Python", "后端开发"],
        "city_code": ["北京", "上海", "深圳"],
        "custom_city_code": {"苏州": "101190400"},
        "industry": ["互联网", "计算机软件"],
        "experience": ["1-3年", "3-5年"],
        "job_type": "全职",
        "salary": "10-20K",
        "degree": ["本科", "大专"],
        "scale": ["100-499人", "500-999人"],
        "stage": ["未融资", "A轮"],
        "enable_ai": True,
        "filter_dead_hr": True,
        "send_img_resume": False,
        "expected_salary": [15000, 25000],
        "wait_time": "5s",
        "dead_status": ["3天前活跃", "本周活跃"]
    }
    
    # 创建配置对象
    config = BossConfig.from_dict(sample_config)
    config.init()
    
    logger.info("初始化后的配置:")
    logger.info(f"城市代码: {config.city_code}")
    logger.info(f"工作类型代码: {config.job_type}")
    logger.info(f"薪资代码: {config.salary}")
    logger.info(f"工作经验代码: {config.experience}")
    logger.info(f"学历代码: {config.degree}")
    logger.info(f"从dict加载的配置:{config.to_dict()}")

    config2 = load_config_from_yaml("boss/config.yaml")
    logger.info("从YAML文件加载的配置: %s", config2)