import logging
import time
from typing import Optional
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import Page

from boss_config import BossConfig,AIConfig
from job import Job
from ai_filter import AiFilter
from playwright_util import PlaywrightUtil
from logger import log


class ResumeSubmission:
    """Boss直聘简历投递类"""
    
    @classmethod
    def resume_submission(cls, page: Page, keyword: str, job: Job, config: BossConfig, ai_config:AIConfig, result_list: list) -> str:
        """
        简历投递方法
        
        Args:
            page: 当前页面对象
            keyword: 搜索关键词
            job: 职位信息
            config: 配置对象
            result_list: 结果列表
            
        Returns:
            bool: 投递是否成功
        """
        PlaywrightUtil.sleep(1)
        detail_page = page

        try:
            # 0.AI 检查职位是否符合要求
            ai_result = None
            if config.enable_ai:
                jd = job.job_info
                if jd and jd.strip():
                    ai_result = cls.check_job(keyword, job.job_name, jd, config, ai_config)

            if ai_result and ai_result.result == False:
                log.info("AI认为不合适")
                return "ai_filtered"
            else:
                log.info("AI认为匹配,开始投递")

            # # 1. 查找"查看更多信息"按钮（必须存在且新开页）
            # more_info_btn = page.locator("a.more-job-btn")
            # if more_info_btn.count() == 0:
            #     log.warning("未找到'查看更多信息'按钮，跳过...")
            #     return False
            #
            # # 强制用js新开tab
            # href = more_info_btn.first.get_attribute("href")
            # if not href or not href.startswith("/job_detail/"):
            #     log.warning("未获取到岗位详情链接，跳过...")
            #     return False
            #
            # detail_url = urljoin("https://www.zhipin.com", href)
            #
            # # 2. 新开详情页
            # detail_page = page.context.new_page()
            # detail_page.goto(detail_url)
            PlaywrightUtil.sleep(1)  # 页面加载

            # 3. 查找"立即沟通"按钮
            chat_btn = detail_page.locator("a.btn-startchat, a.op-btn-chat")
            found_chat_btn = False
            for i in range(5):
                if chat_btn.count() > 0:
                    text_content = chat_btn.first.text_content()
                    if text_content and "立即沟通" in text_content:
                        found_chat_btn = True
                        break
                PlaywrightUtil.sleep(1)
            
            if not found_chat_btn:
                log.warning("未找到立即沟通按钮，跳过岗位: %s", job.job_name)
                # detail_page.close()
                return "page_error"
            
            chat_btn.first.click()
            PlaywrightUtil.sleep(1)

            # 4. 等待聊天输入框
            input_locator = detail_page.locator("div#chat-input.chat-input[contenteditable='true'], textarea.input-area")
            input_ready = False
            for i in range(10):
                if input_locator.count() > 0 and input_locator.first.is_visible():
                    input_ready = True
                    break
                PlaywrightUtil.sleep(1)
            
            if not input_ready:
                log.warning("聊天输入框未出现，跳过: %s", job.job_name)
                # detail_page.close()
                return "page_error"

            # 5. AI智能生成打招呼语
            # ai_result = None
            # log.info(f"enable_ai { config.enable_ai}")
            # if config.enable_ai:
            #     jd = job.job_info
            #     if jd and jd.strip():
            #         ai_result = cls.check_job(keyword, job.job_name, jd, config)
            
            say_hi = config.say_hi.replace("[\r\n]", "")
            if ai_result and ai_result.result and cls.is_valid_string(ai_result.message):
                message = ai_result.message
            else:
                message = say_hi

            # 6. 输入打招呼语
            input_element = input_locator.first
            input_element.click()
            
            # 判断元素类型并输入文本
            tag_name = input_element.evaluate("el => el.tagName.toLowerCase()")
            if tag_name == "textarea":
                input_element.fill(message)
            else:
                input_element.evaluate("(el, msg) => el.innerText = msg", message)

            # 7. 发送图片简历（可选）
            img_resume = False
            if config.send_img_resume:
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

            # 8. 点击发送按钮
            send_btn = detail_page.locator("div.send-message, button[type='send'].btn-send, button.btn-send")
            send_success = False
            if send_btn.count() > 0:
                send_btn.first.click()
                PlaywrightUtil.sleep(1)
                send_success = True
            else:
                log.warning("未找到发送按钮，自动跳过！岗位：%s", job.job_name)

            log.info("投递完成 | 岗位：%s | 招呼语：%s | 图片简历：%s", 
                       job.job_name, message, "已发送" if img_resume else "未发送")

            # 9. 关闭详情页，回到主页面
            # detail_page.close()
            PlaywrightUtil.sleep(1)

            # 10. 成功投递加入结果
            if send_success:
                result_list.append(job)
                return "post_ok"
            else:
                return "post_failure"

        except Exception as e:
            log.error("简历投递过程中出现异常: %s", e)
            # 确保在异常时关闭详情页
            # try:
            #     if 'detail_page' in locals():
            #         detail_page.close()
            # except:
            #     pass
            return "post_eror"

    @classmethod
    def check_job(cls, keyword: str, job_name: str, jd: str, config: BossConfig, ai_config:AIConfig) -> Optional[AiFilter]:
        """
        检查职位是否符合要求（AI过滤）
        
        Args:
            keyword: 搜索关键词
            job_name: 职位名称
            jd: 职位描述
            config: 配置对象
            
        Returns:
            AiFilter: AI过滤结果
        """
        # 这里需要实现AI服务调用
        # 暂时返回None，需要根据实际情况实现
        try:
            from ai_service import AIService
            import json
            bot = AIService(ai_config)
            res = bot.chat(jd)
            if res:
                obj = json.loads(res)
                return AiFilter(obj["match"], obj["hi"])
            else:
                return None
        except Exception as e:
            log.error("AI检查职位失败: %s", e)
            return None

    @classmethod
    def is_valid_string(cls, text: str) -> bool:
        """
        检查字符串是否有效
        
        Args:
            text: 要检查的字符串
            
        Returns:
            bool: 是否有效
        """
        return text is not None and text.strip() != ""

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

    @classmethod
    def safe_resume_submission(cls, page: Page, keyword: str, job: Job, config: BossConfig, result_list: list, max_retries: int = 2) -> bool:
        """
        安全的简历投递方法，包含重试机制
        
        Args:
            page: 当前页面对象
            keyword: 搜索关键词
            job: 职位信息
            config: 配置对象
            result_list: 结果列表
            max_retries: 最大重试次数
            
        Returns:
            bool: 投递是否成功
        """
        for attempt in range(max_retries):
            try:
                log.info("尝试投递职位 '%s' (第%d次尝试)", job.job_name, attempt + 1)
                
                success = cls.resume_submission(page, keyword, job, config, result_list)
                
                if success:
                    log.info("成功投递职位 '%s'", job.job_name)
                    return True
                else:
                    log.warning("第%d次投递职位 '%s' 失败", attempt + 1, job.job_name)
                    
            except Exception as e:
                log.error("第%d次投递职位 '%s' 时出现异常: %s", attempt + 1, job.job_name, e)
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # 递增等待时间
                log.info("%d秒后重试投递...", wait_time)
                time.sleep(wait_time)
        
        log.error("经过%d次尝试后投递职位 '%s' 失败", max_retries, job.job_name)
        return False


# 简化版本 - 可以直接使用的函数
def resume_submission(page: Page, keyword: str, job: Job, config: BossConfig, result_list: list) -> bool:
    """
    简历投递函数（简化版本）
    
    Args:
        page: 当前页面对象
        keyword: 搜索关键词
        job: 职位信息
        config: 配置对象
        result_list: 结果列表
        
    Returns:
        bool: 投递是否成功
    """
    return ResumeSubmission.resume_submission(page, keyword, job, config, result_list)

def safe_resume_submission(page: Page, keyword: str, job: Job, config: BossConfig, result_list: list, max_retries: int = 2) -> bool:
    """
    安全的简历投递函数
    
    Args:
        page: 当前页面对象
        keyword: 搜索关键词
        job: 职位信息
        config: 配置对象
        result_list: 结果列表
        max_retries: 最大重试次数
        
    Returns:
        bool: 投递是否成功
    """
    return ResumeSubmission.safe_resume_submission(page, keyword, job, config, result_list, max_retries)


# 使用示例
if __name__ == "__main__":
    # 示例用法
    from BossConfig import BossConfig
    
    # 创建示例配置
    sample_config = BossConfig(
        enable_ai=True,
        say_hi="您好，我对这个职位很感兴趣",
        send_img_resume=False
    )
    
    # 创建示例职位
    sample_job = Job(
        job_name="Python开发工程师",
        job_info="负责Python后端开发...",
        company_name="示例公司",
        salary="15-25K"
    )
    
    # 在实际使用时，需要传入真实的page对象
    # result = resume_submission(page, "Python", sample_job, sample_config, [])
    # print(f"投递结果: {result}")
    
    print("简历投递模块加载完成")
