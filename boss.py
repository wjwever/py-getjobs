import json
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Optional, Any

from playwright.sync_api import Page, Locator

from boss_enum import BossEnum
from boss_config import BossConfig, load_config_from_yaml, AIConfig
from playwright_util import PlaywrightUtil, DeviceType
from locators import Locators
from job import Job
from logger import log
from resume_submission import ResumeSubmission

class Boss:
    """Boss直聘自动化主类"""

    # 常量定义
    HOME_URL = "https://www.zhipin.com"
    BASE_URL = "https://www.zhipin.com/web/geek/job?"
    DATA_PATH = "data/blacklist.json"
    COOKIE_PATH = "data/cookie.json"

    # 类变量
    black_companies: Set[str] = set()
    black_recruiters: Set[str] = set()
    black_jobs: Set[str] = set()
    result_list: List[Job] = []
    start_date: Optional[datetime] = None
    config: BossConfig
    ai_config: AIConfig

    ##### login start
    @classmethod
    def login(cls):
        """登录Boss直聘"""
        log.info("打开Boss直聘网站中...")

        page = PlaywrightUtil.get_page_object()
        page.goto(cls.HOME_URL)
        PlaywrightUtil.sleep(1)

        # 检查滑块验证
        cls.wait_for_slider_verify(page)

        if PlaywrightUtil.is_cookie_valid(cls.COOKIE_PATH):
            PlaywrightUtil.load_cookies(cls.COOKIE_PATH)
            page.reload()
            PlaywrightUtil.sleep(1)
            cls.wait_for_slider_verify(page)
            # 启用反检测模式
            PlaywrightUtil.init_stealth()

        if cls.is_login_required():
            log.error("cookie失效，尝试扫码登录...")
            cls.scan_login()

    @classmethod
    def wait_for_slider_verify(cls, page: Page):
        """等待滑块验证完成"""
        SLIDER_URL = "https://www.zhipin.com/web/user/safe/verify-slider"

        # 最多等待5分钟（防呆，防止死循环）
        start_time = time.time()
        timeout = 5 * 60  # 5分钟

        while True:
            current_url = page.url
            if current_url and current_url.startswith(SLIDER_URL):
                print("\n【滑块验证】请手动完成Boss直聘滑块验证，通过后在控制台回车继续…")
                try:
                    # 等待用户输入回车
                    input("请完成滑块验证后按回车键继续...")
                except Exception as e:
                    log.error(f"等待滑块验证输入异常: {e}")

                # 等待1秒让页面有时间跳转
                time.sleep(1)
                # 验证通过后页面url会变，循环再检测一次
                continue

            # 检查是否超时
            if (time.time() - start_time) > timeout:
                raise RuntimeError("滑块验证超时！")

            break

    @classmethod
    def scan_login(cls):
        """扫码登录"""
        # 访问登录页面
        page = PlaywrightUtil.get_page_object()
        page.goto(cls.HOME_URL + "/web/user/?ka=header-login")
        PlaywrightUtil.sleep(1)

        # 1. 如果已经登录，则直接返回
        try:
            login_btn_locator = page.locator(Locators.LOGIN_BTN)
            if login_btn_locator.count() > 0 and login_btn_locator.text_content() != "登录":
                log.info("已经登录，直接开始投递...")
                return
        except Exception:
            pass

        log.info("等待登录...")

        # 2. 定位二维码登录的切换按钮
        try:
            scan_button = page.locator(Locators.LOGIN_SCAN_SWITCH)
            scan_button.click()

            # 3. 登录逻辑
            login_success = False

            # 4. 记录开始时间，用于判断10分钟超时
            start_time = time.time()
            timeout = 10 * 60  # 10分钟

            while not login_success:
                # 判断是否超时
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    log.error("超过10分钟未完成登录，程序退出...")
                    exit(1)

                try:
                    # 判断页面上是否出现职位列表容器
                    job_list = page.locator("div.job-list-container")
                    if job_list.is_visible():
                        login_success = True
                        log.info("用户已登录！")
                        # 登录成功，保存Cookie
                        PlaywrightUtil.save_cookies(cls.COOKIE_PATH)
                        break

                    # 检查是否有其他登录成功标志
                    current_url = page.url
                    if "www.zhipin.com" in current_url and "login" not in current_url:
                        login_success = True
                        log.info("检测到已跳转到主页，登录成功！")
                        PlaywrightUtil.save_cookies(cls.COOKIE_PATH)
                        break

                except Exception as e:
                    log.error(f"检测元素时异常: {e}")

                # 每2秒检查一次
                time.sleep(2)

        except Exception as e:
            log.error("未找到二维码登录按钮，登录失败", exc_info=True)

    @classmethod
    def is_login_required(cls) -> bool:
        """检查是否需要登录"""
        try:
            page = PlaywrightUtil.get_page_object()
            button_locator = page.locator(Locators.LOGIN_BTNS)

            if button_locator.count() > 0:
                text_content = button_locator.text_content()
                if text_content and "登录" in text_content:
                    return True

        except Exception as e:
            try:
                page = PlaywrightUtil.get_page_object()
                page.locator(Locators.PAGE_HEADER).wait_for()

                error_login_locator = page.locator(Locators.ERROR_PAGE_LOGIN)
                if error_login_locator.count() > 0:
                    error_login_locator.click()
                    return True

            except Exception as ex:
                log.info("没有出现403访问异常")

            log.info("cookie有效，已登录...")
            return False

        return False

    # 增强的登录检查方法
    @classmethod
    def check_login_status(cls) -> bool:
        """综合检查登录状态"""
        page = PlaywrightUtil.get_page_object()

        # 检查多个登录状态指标
        login_indicators = [
            # 未登录指标
            Locators.LOGIN_BTNS,
            "//button[contains(text(), '登录')]",
            "//a[contains(text(), '登录')]",

            # 已登录指标  
            "//li[@class='nav-figure']//img",  # 用户头像
            "//div[contains(@class, 'user-info')]",
            Locators.JOB_LIST_CONTAINER
        ]

        for i, selector in enumerate(login_indicators):
            try:
                element = page.locator(selector)
                if element.count() > 0:
                    if i < 3:  # 前3个是未登录指标
                        if element.first.is_visible():
                            return False  # 需要登录
                    else:  # 后几个是已登录指标
                        if element.first.is_visible():
                            return True  # 已登录
            except Exception:
                continue

        # 通过URL判断
        current_url = page.url
        if "login" in current_url or "signin" in current_url:
            return False

        return True  # 默认认为已登录

    @classmethod
    def safe_login(cls, max_retries: int = 3):
        """安全的登录流程，包含重试机制"""
        for attempt in range(max_retries):
            try:
                log.info(f"登录尝试 {attempt + 1}/{max_retries}")

                # 检查当前是否已登录
                if cls.check_login_status():
                    log.info("当前已处于登录状态")
                    return True

                # 执行登录流程
                cls.login()

                # 验证登录是否成功
                if cls.check_login_status():
                    log.info("登录成功！")
                    return True
                else:
                    log.warning(f"登录验证失败，尝试 {attempt + 1}/{max_retries}")

            except Exception as e:
                log.error(f"登录过程中出现异常: {e}")

            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # 递增等待时间
                log.info(f"{wait_time}秒后重试登录...")
                time.sleep(wait_time)

        log.error(f"经过{max_retries}次尝试后登录失败")
        return False
    ######login end

    @classmethod
    def initialize_files(cls):
        """初始化数据文件"""
        try:
            # 检查数据文件是否存在
            data_file = Path(cls.DATA_PATH)
            if not data_file.exists():
                data_file.parent.mkdir(parents=True, exist_ok=True)
                initial_data = {
                    "blackCompanies": [],
                    "blackRecruiters": [],
                    "blackJobs": []
                }
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)
                log.info(f"创建数据文件: {cls.DATA_PATH}")

            # 检查cookie文件是否存在
            cookie_file = Path(cls.COOKIE_PATH)
            if not cookie_file.exists():
                cookie_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                log.info(f"创建cookie文件: {cls.COOKIE_PATH}")

        except Exception as e:
            log.error(f"创建文件时发生异常: {e}")

    @classmethod
    def main(cls):
        """主方法"""
        cls.initialize_files()
        cls.load_data(cls.DATA_PATH)

        # 初始化配置
        cls.config, cls.ai_config = load_config_from_yaml("data/config.yaml")

        # 使用Playwright获取岗位
        PlaywrightUtil.init(DeviceType.DESKTOP)
        cls.start_date = datetime.now()

        # 登录
        cls.login()

        # 按城市投递
        for city_code in cls.config.city_code:
            cls.post_job_by_city(city_code)

        # 输出结果
        if cls.result_list:
            log.info("新发起聊天公司如下:\n%s", "\n".join(str(job) for job in cls.result_list))
        else:
            log.info("未发起新的聊天...")

        if not cls.config.debugger:
            cls.print_result()

    @classmethod
    def print_result(cls):
        """打印结果并清理资源"""
        duration = datetime.now() - cls.start_date
        message = f"\nBoss投递完成，共发起{len(cls.result_list)}个聊天，用时{cls.format_duration(duration)}"
        log.info(message)

        # 发送消息（如果需要）
        cls.send_message_by_time(message)

        # 保存数据
        cls.save_data(cls.DATA_PATH)
        cls.result_list.clear()

        if not cls.config.debugger:
            PlaywrightUtil.close()

        # 等待日志写入完成
        time.sleep(1)

    @classmethod
    def format_duration(cls, duration) -> str:
        """格式化时间间隔"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}小时{minutes}分{seconds}秒"
        elif minutes > 0:
            return f"{minutes}分{seconds}秒"
        else:
            return f"{seconds}秒"

    @classmethod
    def send_message_by_time(cls, message: str):
        """根据时间发送消息（占位实现）"""
        # 这里可以实现邮件、微信通知等功能
        pass

    @classmethod
    def post_job_by_city(cls, city_code: str):
        """按城市投递职位"""
        search_url = cls.get_search_url(city_code)

        for keyword in cls.config.keywords:
            post_count = 0
            encoded_keyword = urllib.parse.quote(keyword)

            url = search_url + "&query=" + encoded_keyword
            log.info("投递地址: %s", search_url + "&query=" + keyword)

            page = PlaywrightUtil.get_page_object()
            page.goto(url)
            PlaywrightUtil.sleep(2)

            # 1. 滚动到底部，加载所有岗位卡片
            last_count = -1
            while True:
                # 滑动到底部
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                PlaywrightUtil.sleep(1)

                # 获取所有卡片数
                cards = page.locator("//ul[contains(@class, 'rec-job-list')]//li[contains(@class, 'job-card-box')]")
                current_count = cards.count()

                # 判断是否继续滑动
                if current_count == last_count:
                    break
                last_count = current_count

            log.info("【%s】岗位已全部加载，总数:%d", keyword, last_count)

            # 2. 回到页面顶部
            page.evaluate("window.scrollTo(0, 0);")
            PlaywrightUtil.sleep(1)

            # 3. 逐个遍历所有岗位
            cards = page.locator("//ul[contains(@class, 'rec-job-list')]//li[contains(@class, 'job-card-box')]")
            count = cards.count()

            for i in range(count):
                # 重新获取卡片，避免元素过期
                cards = page.locator("//ul[contains(@class, 'rec-job-list')]//li[contains(@class, 'job-card-box')]")
                cards.nth(i).click()
                PlaywrightUtil.sleep(1)

                # 等待详情内容加载
                detail_box = page.locator("div[class*='job-detail-box']")
                detail_box.wait_for(timeout=4000)

                # 提取职位信息
                job_name = cls.safe_text(detail_box, "span[class*='job-name']")
                if any(black_job in job_name for black_job in cls.black_jobs):
                    continue

                job_salary_raw = cls.safe_text(detail_box, "span.job-salary")
                job_salary = cls.decode_salary(job_salary_raw)

                tags = cls.safe_all_text(detail_box, "ul[class*='tag-list'] > li")
                job_desc = cls.safe_text(detail_box, "p.desc")
                #log.info("job_desc:%s", job_desc)

                boss_name_raw = cls.safe_text(detail_box, "h2[class*='name']")
                boss_name, boss_active = cls.split_boss_name(boss_name_raw)

                boss_title_raw = cls.safe_text(detail_box, "div[class*='boss-info-attr']")
                boss_company, boss_job_title = cls.split_boss_title(boss_title_raw)
                log.info("%s %s %s %s", boss_company, boss_name, boss_job_title, job_salary)

                if any(dead_status in boss_active for dead_status in cls.config.dead_status):
                    log.info("boss is not active")
                    continue

                if any(black_company in boss_company for black_company in cls.black_companies):
                    log.info("black company: %s", boss_company)
                    continue
                if any(black_recruiter in boss_job_title for black_recruiter in cls.black_recruiters):
                    log.info("black recruiter:%s", boss_job_title)
                    continue

                # 创建Job对象
                job = Job(
                    job_name=job_name,
                    salary=job_salary,
                    job_area=", ".join(tags),
                    company_name=boss_company,
                    recruiter=boss_name,
                    job_info=job_desc
                )

                # 投递简历
                # cls.resume_submission(page, keyword, job)
                if ResumeSubmission.resume_submission(page, keyword, job, cls.config, cls.ai_config, cls.result_list):
                    post_count += 1

            log.info("【%s】岗位已投递完毕！已投递岗位数量:%d", keyword, post_count)

    @classmethod
    def decode_salary(cls, text: str) -> str:
        """解码薪资字体"""
        font_map = {
            '': '0', '': '1', '': '2', '': '3', '': '4',
            '': '5', '': '6', '': '7', '': '8', '': '9'
        }
        result = []
        for char in text:
            result.append(font_map.get(char, char))
        return ''.join(result)

    @classmethod
    def safe_text(cls, root: Locator, selector: str) -> str:
        """安全获取单个文本内容"""
        node = root.locator(selector)
        try:
            if node.count() > 0 and node.text_content():
                return node.text_content().strip()
        except Exception:
            pass
        return ""

    @classmethod
    def safe_all_text(cls, root: Locator, selector: str) -> List[str]:
        """安全获取多个文本内容"""
        try:
            return root.locator(selector).all_text_contents()
        except Exception:
            return []

    @classmethod
    def split_boss_name(cls, raw: str) -> tuple[str, str]:
        """拆分Boss姓名和活跃状态"""
        boss_parts = raw.strip().split()
        boss_name = boss_parts[0] if boss_parts else ""
        boss_active = " ".join(boss_parts[1:]) if len(boss_parts) > 1 else ""
        return boss_name, boss_active

    @classmethod
    def split_boss_title(cls, raw: str) -> tuple[str, str]:
        """拆分Boss公司和职位"""
        parts = raw.strip().split(" · ")
        company = parts[0] if parts else ""
        job = parts[1] if len(parts) > 1 else ""
        return company, job

    @classmethod
    def get_search_url(cls, city_code: str) -> str:
        """构建搜索URL"""
        from job_util import JobUtils  # 需要创建这个工具类

        return (cls.BASE_URL + 
            JobUtils.append_param("city", city_code) +
            JobUtils.append_param("jobType", cls.config.job_type) +
            JobUtils.append_param("salary", cls.config.salary) +
            JobUtils.append_list_param("experience", cls.config.experience) +
            JobUtils.append_list_param("degree", cls.config.degree) +
            JobUtils.append_list_param("scale", cls.config.scale) +
            JobUtils.append_list_param("industry", cls.config.industry) +
            JobUtils.append_list_param("stage", cls.config.stage))

    @classmethod
    def save_data(cls, path: str):
        """保存数据到文件"""
        try:
            cls.update_list_data()
            data = {
                "blackCompanies": list(cls.black_companies),
                "blackRecruiters": list(cls.black_recruiters),
                "blackJobs": list(cls.black_jobs)
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error("保存【%s】数据失败！%s", path, e)

    @classmethod
    def update_list_data(cls):
        """更新黑名单数据"""
        page = PlaywrightUtil.get_page_object()
        page.goto("https://www.zhipin.com/web/geek/chat")
        PlaywrightUtil.sleep(3)

        should_break = False
        while not should_break:
            try:
                bottom_locator = page.locator(Locators.FINISHED_TEXT)
                if bottom_locator.count() > 0 and "没有更多了" in bottom_locator.text_content():
                    should_break = True
            except Exception:
                pass

            items = page.locator(Locators.CHAT_LIST_ITEM)
            item_count = items.count()

            for i in range(item_count):
                try:
                    company_elements = page.locator(Locators.COMPANY_NAME_IN_CHAT)
                    message_elements = page.locator(Locators.LAST_MESSAGE)

                    if i >= company_elements.count() or i >= message_elements.count():
                        break

                    company_name = None
                    message = None
                    retry_count = 0

                    while retry_count < 2:
                        try:
                            company_name = company_elements.nth(i).text_content()
                            message = message_elements.nth(i).text_content()
                            break
                        except Exception:
                            retry_count += 1
                            if retry_count >= 2:
                                log.info("尝试获取元素文本2次失败，放弃本次获取")
                                break
                            log.info("页面元素已变更，正在重试第%d次获取元素文本...", retry_count)
                            PlaywrightUtil.sleep(1)

                    if company_name and message:
                        match = any(keyword in message for keyword in ["不", "感谢", "但", "遗憾", "需要本", "对不"])
                        nomatch = any(keyword in message for keyword in ["不是", "不生"])

                        if match and not nomatch:
                            log.info("黑名单公司：【%s】，信息：【%s】", company_name, message)
                            if any(black_company in company_name for black_company in cls.black_companies):
                                continue

                            company_name = company_name.replace("...", "")
                            # 简单的汉字或字母匹配
                            if any(char.isalpha() for char in company_name):
                                cls.black_companies.add(company_name)

                except Exception as e:
                    log.error("寻找黑名单公司异常...%s", e)

            try:
                scroll_element = page.locator(Locators.SCROLL_LOAD_MORE)
                if scroll_element.count() > 0:
                    scroll_element.scroll_into_view_if_needed()
                else:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            except Exception as e:
                log.error("滚动元素出错%s", e)
                break

        log.info("黑名单公司数量：%d", len(cls.black_companies))

    @classmethod
    def load_data(cls, path: str):
        """从文件加载数据"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            cls.parse_json(data)
        except Exception as e:
            log.error("读取【%s】数据失败！%s", path, e)

    @classmethod
    def parse_json(cls, data: Dict[str, Any]):
        """解析JSON数据"""
        cls.black_companies = set(data.get("blackCompanies", []))
        cls.black_recruiters = set(data.get("blackRecruiters", []))
        cls.black_jobs = set(data.get("blackJobs", []))

    # 由于代码量很大，这里只展示了主要方法
    # 其他方法如 resume_submission, login, wait_for_slider_verify 等需要根据之前转换的代码进行整合

# if __name__ == "__main__":
#     Boss.main()
