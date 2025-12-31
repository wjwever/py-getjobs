import json
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Set, Dict, Optional, Any 

from playwright.sync_api import Page 

from boss_config import BossConfig, load_config_from_yaml, AIConfig
from db.db import DatabaseManager
from job_util import Job
from playwright_util import PlaywrightUtil, DeviceType
from locators import Locators
from logger import log

class Boss:
    """Boss直聘自动化主类"""

    # 常量定义
    HOME_URL = "https://www.zhipin.com"
    BASE_URL = "https://www.zhipin.com/web/geek/job?"
    BLACK_LIST = "data/blacklist.json"
    COOKIE_PATH = "data/cookie.json"

    # 类变量
    black_companies: Set[str] = set()
    black_recruiters: Set[str] = set()
    black_jobs: Set[str] = set()
    result_list: List[Job] = []
    start_date: Optional[datetime] = None
    config: BossConfig
    ai_config: AIConfig

    #----------------------------------------------    login start     --------------------------------
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
    #----------------------------------------------------- new jobs ----------------------------------------------
    @classmethod
    def new_jobs(cls):
        """主方法"""
        cls.initialize_files()
        cls.load_black_list(cls.BLACK_LIST)

        # 初始化配置
        cls.config, cls.ai_config = load_config_from_yaml("data/config.yaml")

        # 使用Playwright获取岗位
        PlaywrightUtil.init(DeviceType.DESKTOP)
        cls.start_date = datetime.now()

        # 登录
        cls.login()

        # 按城市投递
        for city_code in cls.config.city_code:
            cls.get_all_jobs_by_city(city_code)

    @classmethod
    def get_all_jobs_by_city(cls, city_code: str):
        """按城市投递职位"""
        search_url = cls.get_search_url(city_code)

        for keyword in cls.config.keywords:
            encoded_keyword = urllib.parse.quote(keyword)

            url = search_url + "&query=" + encoded_keyword
            log.info("投递地址: %s", search_url + "&query=" + keyword)

            page = PlaywrightUtil.get_page_object()
            page.goto(url)
            # PlaywrightUtil.navigate(url)
            PlaywrightUtil.sleep(5)

            # 1. 滚动到底部，加载所有岗位卡片
            results = {}
            while True:
                # 滑动到底部
                page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                PlaywrightUtil.sleep(1)

                # 获取所有卡片数
                #cards = page.locator("//ul[contains(@class, 'rec-job-list')]//li[contains(@class, 'job-card-box')]")
                last_count = len(results)
                results |= cls.get_job_card_info(page)
                current_count = len(results)

                # 判断是否继续滑动
                if current_count == last_count:
                    break
                #last_count = current_count

            log.info("【%s】岗位已全部加载，总数:%d", keyword, last_count)

            # 2. 回到页面顶部
            page.evaluate("window.scrollTo(0, 0);")
            PlaywrightUtil.sleep(1)

            # 3. save to mysql
            db = DatabaseManager()
            for _, v in results.items():
                v["key_word"] = keyword
                db.add_job(v)

    @classmethod
    def get_job_card_info(cls, page) -> dict[str, Any]:
        # 1. 定位所有的 job_card 元素
        job_cards = page.locator(".job-card-box").all()
        
        results = {}

        # 2. 循环遍历提取信息
        for card in job_cards:
            # 提取职位名称
            job_name = card.locator(".job-name").inner_text()
            
            # 提取薪资 (提取到的是加密字符)
            job_salary_raw = card.locator(".job-salary").inner_text()

            job_salary = cls.decode_salary(job_salary_raw)
            
            # 提取标签列表 (5-10年, 本科等)
            tags = card.locator(".tag-list li").all_inner_texts()
            
            # 提取 Boss/公司名称
            boss_name = card.locator(".boss-name").inner_text()
            
            # 提取公司地点 (杭州)
            location = card.locator(".company-location").inner_text()
            
            # 提取详情页链接并拼接完整 URL
            href = card.locator(".job-title a").get_attribute("href")
            job_detail_url = f"https://www.zhipin.com{href}" if href else ""

            # 整理数据
            item = { job_detail_url: {
                "job_name": job_name.strip(),
                "job_salary": job_salary.strip(),
                "tag_list": " ".join(tags),
                "boss_company": boss_name.strip(),
                "company_location": location.strip(),
                "job_detail_url": job_detail_url,
                "referer": page.url
                }
            }
            results |= item
            # print(f"成功提取: {job_name} | {job_salary}")

        # 打印最终结果
        print(f"\n共抓取到 {len(results)} 条数据")
        return results
    #----------------------------------------------------- detail info ----------------------------------------------
    @classmethod
    def update_job_detail_info(cls):
        db = DatabaseManager()
        jobs = db.search_jobs_by_field_value("job_desc", "")

        cls.initialize_files()
        cls.load_black_list(cls.BLACK_LIST)

        # 初始化配置
        cls.config, cls.ai_config = load_config_from_yaml("data/config.yaml")

        # 使用Playwright获取岗位
        PlaywrightUtil.init(DeviceType.DESKTOP)
        cls.start_date = datetime.now()

        # 登录
        cls.login()
        page = PlaywrightUtil.get_page_object()
        for job in jobs:
            cls.fill_in_detail_info(page, job)

    @classmethod
    def fill_in_detail_info(cls, page, job:dict[str, Any]):
        db = DatabaseManager()
        job_id = job['id']
        job_name = job["job_name"]
        boss_company = job["boss_company"]


        job_detail_url = job["job_detail_url"]
        page.goto(job_detail_url, referer=job["referer"])
        PlaywrightUtil.sleep(1)
        section = page.locator(".job-detail-section")
        
        if section.count() == 0:
            db.delete_job(job_id=job_id)
            return

        section = section.first

        try:
            job_sec_text = section.locator(".job-sec-text").first.inner_text()
        except:
            job_sec_text = ""

        # .name 下面包含 span 和 i，我们只需要第一行文本
        boss_name_full = section.locator(".job-boss-info .name").inner_text()
        boss_name = boss_name_full.split('\n')[0].strip()

        attr_text = section.locator(".boss-info-attr").inner_text()
        # 使用中点 '·' 分割字符串
        if "·" in attr_text:
            company, boss_title = [item.strip() for item in attr_text.split("·")]
        else:
            company, boss_title = attr_text.strip(), ""

        try:
            active_time = section.locator(".boss-active-time").inner_text()
        except:
            active_time = ""

        try:
            skills = section.locator('ul.job-keyword-list li').all_text_contents()
        except:
            skills = ""

        detail_info = {
            "boss_company": company,
            "boss_name": boss_name,
            "boss_title": boss_title,
            "boss_active": active_time,
            "job_desc": job_sec_text.strip(),
            "skills" : " ".join(skills)
        }
        log.info(f"提取到的职位详情: {detail_info}")
        db.update_job(job_id, detail_info)

        if any(black_job in job_name for black_job in cls.black_jobs):
            db.add_post_record(job_id, "black_job", "")

        elif any(black_company in boss_company for black_company in cls.black_companies):
            db.add_post_record(job_id, "black_company", "")

        elif any(black_recruiter in boss_title for black_recruiter in cls.black_recruiters):
            db.add_post_record(job_id, "black_recruiter")

        elif any(dead_status in active_time for dead_status in cls.config.dead_status):
            db.add_post_record(job_id, "boss is not active", "")

        # 投递简历
        # status = ResumeSubmission.resume_submission(page, keyword, job_info, cls.config, cls.ai_config, cls.result_list)
        # db.add_post_record(job_id, status)
    #----------------------------------------------------- post_jobs ----------------------------------------------
    @classmethod
    def post_jobs(cls):
        db = DatabaseManager()
        jobs = db.get_active_jobs()

        cls.initialize_files()
        cls.load_black_list(cls.BLACK_LIST)

        # 初始化配置
        cls.config, cls.ai_config = load_config_from_yaml("data/config.yaml")

        # 使用Playwright获取岗位
        PlaywrightUtil.init(DeviceType.DESKTOP)
        cls.start_date = datetime.now()

        # 登录
        cls.login()
        page = PlaywrightUtil.get_page_object()
        for job in jobs:
            cls.post_job(page, job)

    @classmethod
    def post_job(cls, page, job:dict[str, Any]):
        job_id = job["id"]
        if not job["job_desc"]:
            log.error(f"jobid:{job_id} empty job desc")
            return

        db = DatabaseManager()
        say_hi = cls.config.say_hi.replace("[\r\n]", "")
        match:bool = True
        ai_result:str = ""
        if cls.config.enable_ai:
            try:
                from ai_service import AIService
                bot = AIService(cls.ai_config)
                ai_result = bot.chat(job['job_desc'])
                obj = json.loads(ai_result)
                match = obj["match"]
                say_hi = obj["hi"]
            except Exception as e:
                log.error(f"ai chat error {e}")

        if match == False:
            db.add_post_record(job_id, "ai_filtered", ai_result)
            return

        try:
            page.goto(job["job_detail_url"], referer=job["referer"])
            PlaywrightUtil.sleep(3)  # 页面加载
            detail_page = page

            # 3. 查找"立即沟通"按钮
            chat_btn = detail_page.locator("a.btn-startchat, a.op-btn-chat")
            found_chat_btn = False
            for _ in range(10):
                if chat_btn.count() > 0:
                    text_content = chat_btn.first.text_content()
                    if text_content and "立即沟通" in text_content:
                        found_chat_btn = True
                        break
                PlaywrightUtil.sleep(3)
            
            if not found_chat_btn:
                log.warning("未找到立即沟通按钮，跳过岗位: %d", job_id)
                db.add_post_record(job_id, "page_error", ai_result)
                return
            
            chat_btn.first.click()
            PlaywrightUtil.sleep(1)

            # 4. 等待聊天输入框
            input_locator = detail_page.locator("div#chat-input.chat-input[contenteditable='true'], textarea.input-area")
            input_ready = False
            for _ in range(10):
                if input_locator.count() > 0 and input_locator.first.is_visible():
                    input_ready = True
                    break
                PlaywrightUtil.sleep(3)
            
            if not input_ready:
                log.warning("聊天输入框未出现，跳过: %d", job_id)
                db.add_post_record(job_id, "page_error", ai_result)
                return


            # 输入打招呼语
            message = say_hi
            input_element = input_locator.first
            input_element.click()
            
            # 判断元素类型并输入文本
            tag_name = input_element.evaluate("el => el.tagName.toLowerCase()")
            if tag_name == "textarea":
                input_element.fill(message)
            else:
                input_element.evaluate("(el, msg) => el.innerText = msg", message)

            img_resume = False
            if cls.config.send_img_resume:
                try:
                    # 查找图片简历文件
                    resume_path = cls.find_resume_image()
                    if resume_path:
                        log.info("找到图片简历")
                        file_input = detail_page.locator("//div[@aria-label='发送图片']//input[@type='file']")
                        if file_input.count() > 0:
                            file_input.set_input_files(resume_path)
                            img_resume = True
                except Exception as e:
                    log.error("发送图片简历失败: %s", e)

            send_btn = detail_page.locator("div.send-message, button[type='send'].btn-send, button.btn-send")
            send_success = False
            if send_btn.count() > 0:
                send_btn.first.click()
                PlaywrightUtil.sleep(1)
                send_success = True
            else:
                log.warning("未找到发送按钮，自动跳过！岗位：%d", job_id)

            log.info("投递完成 | 岗位：%s | 招呼语：%s | 图片简历：%s", 
                        job["job_name"], message, "已发送" if img_resume else "未发送")

            PlaywrightUtil.sleep(1)

            if send_success:
                db.add_post_record(job_id, "post_ok", ai_result)
            else:
                db.add_post_record(job_id, "post_failure", ai_result)
            return
        except Exception as e:
            log.error(f"post job exception: {e}")
            db.add_post_record(job_id, "post_failure", ai_result)

    @classmethod
    def find_resume_image(cls) -> Optional[Path]:
        """
        查找图片简历文件
        
        Returns:
            Path: 图片文件路径，如果未找到返回None
        """
        # 在多个可能的位置查找简历图片
        possible_paths = [
            Path("resume.jpg"),
            Path("resources/resume.jpg"),
            Path("src/main/resources/resume.jpg"),
            Path("static/resume.jpg"),
            Path("assets/resume.jpg"),
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        log.warning("未找到简历图片文件")
        return None

    #----------------------------------------------------- update black list ----------------------------------------------
    @classmethod
    def save_black_list(cls):
        """保存黑名单数据"""
        path = cls.BLACK_LIST
        try:
            cls.update_black_list()
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
    def update_black_list(cls):
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
                        match = any(keyword in message for keyword in ["但是很遗憾", "不匹配"])
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

    #----------------------------------------------------- tools ----------------------------------------------
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
    def load_black_list(cls, path: str):
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

    @classmethod
    def initialize_files(cls):
        """初始化数据文件"""
        try:
            # 检查数据文件是否存在
            data_file = Path(cls.BLACK_LIST)
            if not data_file.exists():
                data_file.parent.mkdir(parents=True, exist_ok=True)
                initial_data = {
                    "blackCompanies": [],
                    "blackRecruiters": [],
                    "blackJobs": []
                }
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, ensure_ascii=False, indent=2)
                log.info(f"创建数据文件: {cls.BLACK_LIST}")

            # 检查cookie文件是否存在
            cookie_file = Path(cls.COOKIE_PATH)
            if not cookie_file.exists():
                cookie_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                log.info(f"创建cookie文件: {cls.COOKIE_PATH}")

        except Exception as e:
            log.error(f"创建文件时发生异常: {e}")

    #----------------------------------------------------- abandon ----------------------------------------------
    # @classmethod
    # def main(cls):
    #     """主方法"""
    #     cls.initialize_files()
    #     cls.load_black_list(cls.BLACK_LIST)
    #
    #     # 初始化配置
    #     cls.config, cls.ai_config = load_config_from_yaml("data/config.yaml")
    #
    #     # 使用Playwright获取岗位
    #     PlaywrightUtil.init(DeviceType.DESKTOP)
    #     cls.start_date = datetime.now()
    #
    #     # 登录
    #     cls.login()
    #
    #     # 按城市投递
    #     for city_code in cls.config.city_code:
    #         cls.post_job_by_city(city_code)
    #
    #     # 输出结果
    #     if cls.result_list:
    #         log.info("新发起聊天公司如下:\n%s", "\n".join(str(job) for job in cls.result_list))
    #     else:
    #         log.info("未发起新的聊天...")
    #
    #     if not cls.config.debugger:
    #         cls.print_result()

    # @classmethod
    # def print_result(cls):
    #     """打印结果并清理资源"""
    #     duration = datetime.now() - cls.start_date
    #     message = f"\nBoss投递完成，共发起{len(cls.result_list)}个聊天，用时{cls.format_duration(duration)}"
    #     log.info(message)
    #
    #     # 发送消息（如果需要）
    #     cls.send_message_by_time(message)
    #
    #     # 保存数据
    #     cls.save_data(cls.BLACK_LIST)
    #     cls.result_list.clear()
    #
    #     if not cls.config.debugger:
    #         PlaywrightUtil.close()
    #
    #     # 等待日志写入完成
    #     time.sleep(1)

    # @classmethod
    # def format_duration(cls, duration) -> str:
    #     """格式化时间间隔"""
    #     total_seconds = int(duration.total_seconds())
    #     hours = total_seconds // 3600
    #     minutes = (total_seconds % 3600) // 60
    #     seconds = total_seconds % 60
    #
    #     if hours > 0:
    #         return f"{hours}小时{minutes}分{seconds}秒"
    #     elif minutes > 0:
    #         return f"{minutes}分{seconds}秒"
    #     else:
    #         return f"{seconds}秒"

    # @classmethod
    # def send_message_by_time(cls, message: str):
    #     """根据时间发送消息（占位实现）"""
    #     # 这里可以实现邮件、微信通知等功能
    #     pass
    
    # @classmethod
    # def post_job_by_city(cls, city_code: str):
    #     """按城市投递职位"""
    #     search_url = cls.get_search_url(city_code)
    #
    #     for keyword in cls.config.keywords:
    #         post_count = 0
    #         encoded_keyword = urllib.parse.quote(keyword)
    #
    #         url = search_url + "&query=" + encoded_keyword
    #         log.info("投递地址: %s", search_url + "&query=" + keyword)
    #
    #         page = PlaywrightUtil.get_page_object()
    #         page.goto(url)
    #         PlaywrightUtil.sleep(2)
    #
    #         # 1. 滚动到底部，加载所有岗位卡片
    #         last_count = -1
    #         while True:
    #             # 滑动到底部
    #             page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    #             PlaywrightUtil.sleep(1)
    #
    #             # 获取所有卡片数
    #             cards = page.locator("//ul[contains(@class, 'rec-job-list')]//li[contains(@class, 'job-card-box')]")
    #             current_count = cards.count()
    #
    #             # 判断是否继续滑动
    #             if current_count == last_count:
    #                 break
    #             last_count = current_count
    #
    #         log.info("【%s】岗位已全部加载，总数:%d", keyword, last_count)
    #
    #         # 2. 回到页面顶部
    #         page.evaluate("window.scrollTo(0, 0);")
    #         PlaywrightUtil.sleep(1)
    #
    #         # 3. 逐个遍历所有岗位
    #         cards = page.locator("//ul[contains(@class, 'rec-job-list')]//li[contains(@class, 'job-card-box')]")
    #         count = cards.count()
    #
    #         for i in range(count):
    #             # 重新获取卡片，避免元素过期
    #             cards = page.locator("//ul[contains(@class, 'rec-job-list')]//li[contains(@class, 'job-card-box')]")
    #             cards.nth(i).click()
    #             PlaywrightUtil.sleep(1)
    #
    #             # 等待详情内容加载
    #             detail_box = page.locator("div[class*='job-detail-box']")
    #             detail_box.wait_for(timeout=4000)
    #
    #             # 提取职位信息
    #             job_name = cls.safe_text(detail_box, "span[class*='job-name']")
    #             if any(black_job in job_name for black_job in cls.black_jobs):
    #                 continue
    #
    #             job_salary_raw = cls.safe_text(detail_box, "span.job-salary")
    #             job_salary = cls.decode_salary(job_salary_raw)
    #
    #             tags = cls.safe_all_text(detail_box, "ul[class*='tag-list'] > li")
    #             job_desc = cls.safe_text(detail_box, "p.desc")
    #             #log.info("job_desc:%s", job_desc)
    #
    #             boss_name_raw = cls.safe_text(detail_box, "h2[class*='name']")
    #             boss_name, boss_active = cls.split_boss_name(boss_name_raw)
    #
    #             boss_title_raw = cls.safe_text(detail_box, "div[class*='boss-info-attr']")
    #             boss_company, boss_job_title = cls.split_boss_title(boss_title_raw)
    #             log.info("%s %s %s %s", boss_company, boss_name, boss_job_title, job_salary)
    #
    #             if any(dead_status in boss_active for dead_status in cls.config.dead_status):
    #                 log.info("boss is not active")
    #                 continue
    #
    #             if any(black_company in boss_company for black_company in cls.black_companies):
    #                 log.info("black company: %s", boss_company)
    #                 continue
    #             if any(black_recruiter in boss_job_title for black_recruiter in cls.black_recruiters):
    #                 log.info("black recruiter:%s", boss_job_title)
    #                 continue
    #
    #             # 创建Job对象
    #             job = Job(
    #                 job_name=job_name,
    #                 salary=job_salary,
    #                 job_area=", ".join(tags),
    #                 company_name=boss_company,
    #                 recruiter=boss_name,
    #                 job_info=job_desc
    #             )
    #
    #             # 投递简历
    #             # cls.resume_submission(page, keyword, job)
    #             if ResumeSubmission.resume_submission(page, keyword, job, cls.config, cls.ai_config, cls.result_list):
    #                 post_count += 1
    #
    #         log.info("【%s】岗位已投递完毕！已投递岗位数量:%d", keyword, post_count)

    # @classmethod
    # def safe_text(cls, root: Locator, selector: str) -> str:
    #     """安全获取单个文本内容"""
    #     node = root.locator(selector)
    #     try:
    #         if node.count() > 0 and node.text_content():
    #             return node.text_content().strip()
    #     except Exception:
    #         pass
    #     return ""

    # @classmethod
    # def safe_all_text(cls, root: Locator, selector: str) -> List[str]:
    #     """安全获取多个文本内容"""
    #     try:
    #         return root.locator(selector).all_text_contents()
    #     except Exception:
    #         return []

    # @classmethod
    # def split_boss_name(cls, raw: str) -> tuple[str, str]:
    #     """拆分Boss姓名和活跃状态"""
    #     boss_parts = raw.strip().split()
    #     boss_name = boss_parts[0] if boss_parts else ""
    #     boss_active = " ".join(boss_parts[1:]) if len(boss_parts) > 1 else ""
    #     return boss_name, boss_active

    # @classmethod
    # def split_boss_title(cls, raw: str) -> tuple[str, str]:
    #     """拆分Boss公司和职位"""
    #     parts = raw.strip().split(" · ")
    #     company = parts[0] if parts else ""
    #     job = parts[1] if len(parts) > 1 else ""
    #     return company, job




