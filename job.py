from dataclasses import dataclass
from typing import Optional

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