from enum import Enum
from typing import Optional, Dict, Any
import json

class BossEnum:
    """Boss直聘枚举类"""
    
    class Experience(Enum):
        """工作经验枚举"""
        NULL = ("不限", "0")
        STUDENT = ("在校生", "108")
        GRADUATE = ("应届毕业生", "102")
        UNLIMITED = ("经验不限", "101")
        LESS_THAN_ONE_YEAR = ("1年以下", "103")
        ONE_TO_THREE_YEARS = ("1-3年", "104")
        THREE_TO_FIVE_YEARS = ("3-5年", "105")
        FIVE_TO_TEN_YEARS = ("5-10年", "106")
        MORE_THAN_TEN_YEARS = ("10年以上", "107")
        
        def __init__(self, display_name: str, code: str):
            self._display_name = display_name
            self.code = code
        
        @property
        def display_name(self) -> str:
            """显示名称"""
            return self._display_name
        
        @classmethod
        def get_code(cls, name: str) -> Optional[str]:
            """根据显示名称获取代码"""
            for experience in cls:
                if experience.display_name == name:
                    return experience.code
            return None
        
        @classmethod
        def for_value(cls, value: str) -> 'BossEnum.Experience':
            """根据显示名称获取枚举实例"""
            for experience in cls:
                if experience.display_name == value:
                    return experience
            return cls.NULL
        
        def to_dict(self) -> Dict[str, str]:
            """转换为字典"""
            return {"display_name": self.display_name, "code": self.code}
        
        def __str__(self) -> str:
            return f"{self.display_name}({self.code})"

    class CityCode(Enum):
        """城市代码枚举"""
        NULL = ("不限", "0")
        ALL = ("全国", "100010000")
        
        def __init__(self, display_name: str, code: str):
            self._display_name = display_name
            self.code = code
        
        @property
        def display_name(self) -> str:
            """显示名称"""
            return self._display_name
        
        @classmethod
        def for_value(cls, value: str) -> 'BossEnum.CityCode':
            """根据显示名称获取枚举实例"""
            for city_code in cls:
                if city_code.display_name == value:
                    return city_code
            return cls.NULL
        
        def to_dict(self) -> Dict[str, str]:
            """转换为字典"""
            return {"display_name": self.display_name, "code": self.code}
        
        def __str__(self) -> str:
            return f"{self.display_name}({self.code})"

    class JobType(Enum):
        """职位类型枚举"""
        NULL = ("不限", "0")
        FULL_TIME = ("全职", "1901")
        PART_TIME = ("兼职", "1903")
        
        def __init__(self, display_name: str, code: str):
            self._display_name = display_name
            self.code = code
        
        @property
        def display_name(self) -> str:
            """显示名称"""
            return self._display_name
        
        @classmethod
        def for_value(cls, value: str) -> 'BossEnum.JobType':
            """根据显示名称获取枚举实例"""
            for job_type in cls:
                if job_type.display_name == value:
                    return job_type
            return cls.NULL
        
        def to_dict(self) -> Dict[str, str]:
            """转换为字典"""
            return {"display_name": self.display_name, "code": self.code}
        
        def __str__(self) -> str:
            return f"{self.display_name}({self.code})"

    class Salary(Enum):
        """薪资范围枚举"""
        NULL = ("不限", "0")
        BELOW_3K = ("3K以下", "402")
        FROM_3K_TO_5K = ("3-5K", "403")
        FROM_5K_TO_10K = ("5-10K", "404")
        FROM_10K_TO_20K = ("10-20K", "405")
        FROM_20K_TO_50K = ("20-50K", "406")
        ABOVE_50K = ("50K以上", "407")
        
        def __init__(self, display_name: str, code: str):
            self._display_name = display_name
            self.code = code
        
        @property
        def display_name(self) -> str:
            """显示名称"""
            return self._display_name
        
        @classmethod
        def for_value(cls, value: str) -> 'BossEnum.Salary':
            """根据显示名称获取枚举实例"""
            for salary in cls:
                if salary.display_name == value:
                    return salary
            return cls.NULL
        
        def to_dict(self) -> Dict[str, str]:
            """转换为字典"""
            return {"display_name": self.display_name, "code": self.code}
        
        def __str__(self) -> str:
            return f"{self.display_name}({self.code})"

    class Degree(Enum):
        """学历要求枚举"""
        NULL = ("不限", "0")
        BELOW_JUNIOR_HIGH_SCHOOL = ("初中及以下", "209")
        SECONDARY_VOCATIONAL = ("中专/中技", "208")
        HIGH_SCHOOL = ("高中", "206")
        JUNIOR_COLLEGE = ("大专", "202")
        BACHELOR = ("本科", "203")
        MASTER = ("硕士", "204")
        DOCTOR = ("博士", "205")
        
        def __init__(self, display_name: str, code: str):
            self._display_name = display_name
            self.code = code
        
        @property
        def display_name(self) -> str:
            """显示名称"""
            return self._display_name
        
        @classmethod
        def for_value(cls, value: str) -> 'BossEnum.Degree':
            """根据显示名称获取枚举实例"""
            for degree in cls:
                if degree.display_name == value:
                    return degree
            return cls.NULL
        
        def to_dict(self) -> Dict[str, str]:
            """转换为字典"""
            return {"display_name": self.display_name, "code": self.code}
        
        def __str__(self) -> str:
            return f"{self.display_name}({self.code})"

    class Scale(Enum):
        """公司规模枚举"""
        NULL = ("不限", "0")
        ZERO_TO_TWENTY = ("0-20人", "301")
        TWENTY_TO_NINETY_NINE = ("20-99人", "302")
        ONE_HUNDRED_TO_FOUR_NINETY_NINE = ("100-499人", "303")
        FIVE_HUNDRED_TO_NINE_NINETY_NINE = ("500-999人", "304")
        ONE_THOUSAND_TO_NINE_NINE_NINE_NINE = ("1000-9999人", "305")
        TEN_THOUSAND_ABOVE = ("10000人以上", "306")
        
        def __init__(self, display_name: str, code: str):
            self._display_name = display_name
            self.code = code
        
        @property
        def display_name(self) -> str:
            """显示名称"""
            return self._display_name
        
        @classmethod
        def for_value(cls, value: str) -> 'BossEnum.Scale':
            """根据显示名称获取枚举实例"""
            for scale in cls:
                if scale.display_name == value:
                    return scale
            return cls.NULL
        
        def to_dict(self) -> Dict[str, str]:
            """转换为字典"""
            return {"display_name": self.display_name, "code": self.code}
        
        def __str__(self) -> str:
            return f"{self.display_name}({self.code})"

    class Financing(Enum):
        """融资阶段枚举"""
        NULL = ("不限", "0")
        UNFUNDED = ("未融资", "801")
        ANGEL_ROUND = ("天使轮", "802")
        A_ROUND = ("A轮", "803")
        B_ROUND = ("B轮", "804")
        C_ROUND = ("C轮", "805")
        D_AND_ABOVE = ("D轮及以上", "806")
        LISTED = ("已上市", "807")
        NO_NEED = ("不需要融资", "808")
        
        def __init__(self, display_name: str, code: str):
            self._display_name = display_name
            self.code = code
        
        @property
        def display_name(self) -> str:
            """显示名称"""
            return self._display_name
        
        @classmethod
        def for_value(cls, value: str) -> 'BossEnum.Financing':
            """根据显示名称获取枚举实例"""
            for financing in cls:
                if financing.display_name == value:
                    return financing
            return cls.NULL
        
        def to_dict(self) -> Dict[str, str]:
            """转换为字典"""
            return {"display_name": self.display_name, "code": self.code}
        
        def __str__(self) -> str:
            return f"{self.display_name}({self.code})"

    class Industry(Enum):
        """行业枚举"""
        NULL = ("不限", "0")
        INTERNET = ("互联网", "100020")
        COMPUTER_SOFTWARE = ("计算机软件", "100021")
        CLOUD_COMPUTING = ("云计算", "100029")
        
        def __init__(self, display_name: str, code: str):
            self._display_name = display_name
            self.code = code
        
        @property
        def display_name(self) -> str:
            """显示名称"""
            return self._display_name
        
        @classmethod
        def for_value(cls, value: str) -> 'BossEnum.Industry':
            """根据显示名称获取枚举实例"""
            for industry in cls:
                if industry.display_name == value:
                    return industry
            return cls.NULL
        
        def to_dict(self) -> Dict[str, str]:
            """转换为字典"""
            return {"display_name": self.display_name, "code": self.code}
        
        def __str__(self) -> str:
            return f"{self.display_name}({self.code})"

    # 工具方法
    @classmethod
    def get_all_enums(cls) -> Dict[str, Any]:
        """获取所有枚举类型"""
        return {
            'experience': cls.Experience,
            'city_code': cls.CityCode,
            'job_type': cls.JobType,
            'salary': cls.Salary,
            'degree': cls.Degree,
            'scale': cls.Scale,
            'financing': cls.Financing,
            'industry': cls.Industry
        }
    
    @classmethod
    def get_enum_by_name_and_value(cls, enum_name: str, value: str) -> Optional[Enum]:
        """根据枚举名称和显示名称获取枚举实例"""
        enum_class = cls.get_all_enums().get(enum_name)
        if enum_class:
            return enum_class.for_value(value)
        return None
    
    @classmethod
    def get_code_by_name_and_value(cls, enum_name: str, value: str) -> Optional[str]:
        """根据枚举名称和显示名称获取代码"""
        enum_instance = cls.get_enum_by_name_and_value(enum_name, value)
        if enum_instance:
            return enum_instance.code
        return None


# JSON序列化支持
class BossEnumEncoder(json.JSONEncoder):
    """Boss枚举JSON编码器"""
    
    def default(self, obj):
        if isinstance(obj, Enum) and hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)


# 使用示例
if __name__ == "__main__":
    # 基本使用
    experience = BossEnum.Experience.ONE_TO_THREE_YEARS
    print(f"工作经验: {experience.display_name} -> {experience.code}")
    print(f"枚举名称: {experience.name}")  # 这是Enum内置的name
    
    # 根据显示名称获取代码
    code = BossEnum.Experience.get_code("1-3年")
    print(f"根据显示名称获取代码: {code}")
    
    # 根据显示名称获取枚举实例
    exp_enum = BossEnum.Experience.for_value("1-3年")
    print(f"根据显示名称获取枚举: {exp_enum}")
    
    # 使用工具方法
    salary_code = BossEnum.get_code_by_name_and_value('salary', '10-20K')
    print(f"薪资代码: {salary_code}")
    
    # 遍历所有工作经验
    print("\n所有工作经验:")
    for exp in BossEnum.Experience:
        print(f"  {exp.display_name}: {exp.code}")
    
    # JSON序列化
    job_criteria = {
        "experience": BossEnum.Experience.THREE_TO_FIVE_YEARS,
        "salary": BossEnum.Salary.FROM_10K_TO_20K,
        "degree": BossEnum.Degree.BACHELOR
    }
    
    json_str = json.dumps(job_criteria, cls=BossEnumEncoder, ensure_ascii=False, indent=2)
    print(f"\nJSON序列化:\n{json_str}")