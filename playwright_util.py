"""
Playwright工具类，提供浏览器自动化相关的功能
"""
import json
import random
import time
from pathlib import Path
from enum import Enum
from typing import Optional
from playwright.sync_api import Playwright, Browser, BrowserContext, Page, Locator
from logger import log


class DeviceType(Enum):
    """设备类型枚举"""
    DESKTOP = "desktop"  # 桌面设备
    MOBILE = "mobile"    # 移动设备

class PlaywrightUtil:
    """Playwright工具类"""
    
    # 类变量
    _default_device_type = DeviceType.DESKTOP
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _desktop_context: Optional[BrowserContext] = None
    _mobile_context: Optional[BrowserContext] = None
    _desktop_page: Optional[Page] = None
    _mobile_page: Optional[Page] = None
    
    # 默认超时时间（毫秒）
    DEFAULT_TIMEOUT = 30000
    # 默认等待时间（毫秒）
    DEFAULT_WAIT_TIME = 10000

    @classmethod
    def init(cls, device_type:DeviceType):
        """初始化Playwright及浏览器实例"""
        from playwright.sync_api import sync_playwright
        cls.close()
        
        # 启动Playwright
        cls._playwright = sync_playwright().start()

        # 创建浏览器实例
        cls._browser = cls._playwright.chromium.launch(
            headless=False,  # 非无头模式，可视化调试
            slow_mo=50       # 放慢操作速度，便于调试
        )

        # 创建桌面浏览器上下文
        cls._desktop_context = cls._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        )

        # 创建移动设备浏览器上下文
        cls._mobile_context = cls._browser.new_context(
            viewport={"width": 375, "height": 812},
            device_scale_factor=3.0,
            is_mobile=True,
            has_touch=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        )


        cls.set_default_device_type(device_type)
        # 创建桌面页面
        if cls._default_device_type == DeviceType.DESKTOP:
            cls._desktop_page = cls._desktop_context.new_page()
            cls._desktop_page.set_default_timeout(cls.DEFAULT_TIMEOUT)
        else:
            # 创建移动设备页面
            cls._mobile_page = cls._mobile_context.new_page()
            cls._mobile_page.set_default_timeout(cls.DEFAULT_TIMEOUT)

        log.info("Playwright及浏览器实例初始化完成")

    @classmethod
    def set_default_device_type(cls, device_type: DeviceType):
        """设置默认设备类型"""
        cls._default_device_type = device_type
        log.info(f"已设置默认设备类型为: {device_type}")

    @classmethod
    def _get_page(cls, device_type: DeviceType = None) -> Page:
        """获取当前页面（基于当前设备类型）"""
        if device_type is None:
            device_type = cls._default_device_type
        
        return cls._desktop_page if device_type == DeviceType.DESKTOP else cls._mobile_page

    @classmethod
    def _get_context(cls, device_type: DeviceType = None) -> BrowserContext:
        """获取当前上下文（基于当前设备类型）"""
        if device_type is None:
            device_type = cls._default_device_type
        
        return cls._desktop_context if device_type == DeviceType.DESKTOP else cls._mobile_context

    @classmethod
    def close(cls):
        """关闭Playwright及浏览器实例"""
        if cls._desktop_page:
            cls._desktop_page.close()
        if cls._mobile_page:
            cls._mobile_page.close()
        if cls._desktop_context:
            cls._desktop_context.close()
        if cls._mobile_context:
            cls._mobile_context.close()
        if cls._browser:
            cls._browser.close()
        if cls._playwright:
            cls._playwright.stop()

        log.info("Playwright及浏览器实例已关闭")

    @classmethod
    def navigate(cls, url: str, device_type: DeviceType = None):
        """导航到指定URL"""
        if device_type is None:
            device_type = cls._default_device_type
            
        for _ in range(10):
            try:
                cls._get_page(device_type).goto(url)
                log.info(f"已导航到URL: {url} (设备类型: {device_type})")
                break
            except:
                log.info(f"重试导航到URL: {url} (设备类型: {device_type})")
                pass

    @classmethod
    def mobile_navigate(cls, url: str):
        """移动设备导航到指定URL (兼容旧代码)"""
        cls.navigate(url, DeviceType.MOBILE)

    @classmethod
    def sleep(cls, seconds: int):
        """等待指定时间（秒）"""
        time.sleep(seconds)

    @classmethod
    def sleep_millis(cls, millis: int):
        """等待指定时间（毫秒）"""
        time.sleep(millis / 1000.0)

    @classmethod
    def sleep_by_milli_seconds(cls, milli_seconds: int):
        """兼容SeleniumUtil的sleepByMilliSeconds方法"""
        cls.sleep_millis(milli_seconds)

    @classmethod
    def find_element(cls, selector: str, device_type: DeviceType = None) -> Locator:
        """查找元素"""
        return cls._get_page(device_type).locator(selector)

    @classmethod
    def wait_for_element(cls, selector: str, timeout: int = None, device_type: DeviceType = None) -> Locator:
        """查找元素并等待直到可见"""
        if timeout is None:
            timeout = cls.DEFAULT_WAIT_TIME
            
        locator = cls._get_page(device_type).locator(selector)
        locator.wait_for(timeout=timeout)
        return locator

    @classmethod
    def click(cls, selector: str, device_type: DeviceType = None):
        """点击元素"""
        try:
            cls._get_page(device_type).locator(selector).click()
            log.info(f"已点击元素: {selector} (设备类型: {device_type or cls._default_device_type})")
        except Exception as e:
            log.error(f"点击元素失败: {selector} (设备类型: {device_type or cls._default_device_type})", exc_info=True)

    @classmethod
    def fill(cls, selector: str, text: str, device_type: DeviceType = None):
        """填写表单字段"""
        try:
            cls._get_page(device_type).locator(selector).fill(text)
            log.info(f"已在元素{selector}中输入文本 (设备类型: {device_type or cls._default_device_type})")
        except Exception as e:
            log.error(f"填写表单失败: {selector} (设备类型: {device_type or cls._default_device_type})", exc_info=True)

    @classmethod
    def type_human_like(cls, selector: str, text: str, min_delay: int = 50, max_delay: int = 150, device_type: DeviceType = None):
        """模拟人类输入文本（逐字输入）"""
        try:
            locator = cls._get_page(device_type).locator(selector)
            locator.click()

            for char in text:
                # 计算本次字符输入的延迟时间
                delay = random.randint(min_delay, max_delay)
                # 输入单个字符
                locator.press_sequentially(char, delay=delay)
                
            log.info(f"已模拟人类在元素{selector}中输入文本 (设备类型: {device_type or cls._default_device_type})")
        except Exception as e:
            log.error(f"模拟人类输入失败: {selector} (设备类型: {device_type or cls._default_device_type})", exc_info=True)

    @classmethod
    def get_text(cls, selector: str, device_type: DeviceType = None) -> str:
        """获取元素文本"""
        try:
            return cls._get_page(device_type).locator(selector).text_content() or ""
        except Exception as e:
            log.error(f"获取元素文本失败: {selector} (设备类型: {device_type or cls._default_device_type})", exc_info=True)
            return ""

    @classmethod
    def get_attribute(cls, selector: str, attribute_name: str, device_type: DeviceType = None) -> str:
        """获取元素属性值"""
        try:
            return cls._get_page(device_type).locator(selector).get_attribute(attribute_name) or ""
        except Exception as e:
            log.error(f"获取元素属性失败: {selector}[{attribute_name}] (设备类型: {device_type or cls._default_device_type})", exc_info=True)
            return ""

    @classmethod
    def screenshot(cls, path: str, device_type: DeviceType = None):
        """截取页面截图并保存"""
        try:
            cls._get_page(device_type).screenshot(path=path)
            log.info(f"已保存截图到: {path} (设备类型: {device_type or cls._default_device_type})")
        except Exception as e:
            log.error(f"截图失败 (设备类型: {device_type or cls._default_device_type})", exc_info=True)

    @classmethod
    def screenshot_element(cls, selector: str, path: str, device_type: DeviceType = None):
        """截取特定元素的截图"""
        try:
            cls._get_page(device_type).locator(selector).screenshot(path=path)
            log.info(f"已保存元素截图到: {path} (设备类型: {device_type or cls._default_device_type})")
        except Exception as e:
            log.error(f"元素截图失败: {selector} (设备类型: {device_type or cls._default_device_type})", exc_info=True)

    @classmethod
    def save_cookies(cls, path: str, device_type: DeviceType = None):
        """保存Cookie到文件"""
        try:
            cookies = cls._get_context(device_type).cookies()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=4)
            log.info(f"Cookie已保存到文件: {path} (设备类型: {device_type or cls._default_device_type})")
        except Exception as e:
            log.error(f"保存Cookie失败 (设备类型: {device_type or cls._default_device_type})", exc_info=True)

    @classmethod
    def load_cookies(cls, path: str, device_type: DeviceType = None):
        """从文件加载Cookie"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            cls._get_context(device_type).add_cookies(cookies)
            log.info(f"已从文件加载Cookie: {path} (设备类型: {device_type or cls._default_device_type})")
        except Exception as e:
            log.error(f"加载Cookie失败 (设备类型: {device_type or cls._default_device_type})", exc_info=True)

    @classmethod
    def evaluate(cls, script: str, device_type: DeviceType = None):
        """执行JavaScript代码"""
        try:
            cls._get_page(device_type).evaluate(script)
        except Exception as e:
            log.error(f"执行JavaScript失败 (设备类型: {device_type or cls._default_device_type})", exc_info=True)

    @classmethod
    def wait_for_page_load(cls, device_type: DeviceType = None):
        """等待页面加载完成"""
        page = cls._get_page(device_type)
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_load_state("networkidle")

    @classmethod
    def element_is_visible(cls, selector: str, device_type: DeviceType = None) -> bool:
        """检查元素是否可见"""
        try:
            return cls._get_page(device_type).locator(selector).is_visible()
        except Exception as e:
            return False

    @classmethod
    def select_by_text(cls, selector: str, option_text: str, device_type: DeviceType = None):
        """选择下拉列表选项（通过文本）"""
        cls._get_page(device_type).locator(selector).select_option(label=option_text)

    @classmethod
    def select_by_value(cls, selector: str, value: str, device_type: DeviceType = None):
        """选择下拉列表选项（通过值）"""
        cls._get_page(device_type).locator(selector).select_option(value=value)

    @classmethod
    def get_title(cls, device_type: DeviceType = None) -> str:
        """获取当前页面标题"""
        return cls._get_page(device_type).title()

    @classmethod
    def get_url(cls, device_type: DeviceType = None) -> str:
        """获取当前页面URL"""
        return cls._get_page(device_type).url()

    @classmethod
    def init_stealth(cls, device_type: DeviceType = None):
        """初始化Stealth模式（使浏览器更难被检测为自动化工具）"""
        # 获取当前页面，不重新创建上下文和页面
        page = cls._get_page(device_type)
        
        # 为现有上下文设置额外的HTTP头
        context = cls._get_context(device_type)
        if device_type == DeviceType.DESKTOP or device_type is None:
            context.set_extra_http_headers({
                "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"macOS\"",
                "accept-language": "zh-CN,zh;q=0.9",
                "referer": "https://www.zhipin.com/",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin"
            })
        else:
            context.set_extra_http_headers({
                "sec-ch-ua": "\"Chromium\";v=\"135\", \"Not A(Brand\";v=\"99\"",
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": "\"iOS\"",
                "accept-language": "zh-CN,zh;q=0.9",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "same-origin"
            })

        # 注入反检测脚本
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Window;
        window.navigator.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh']});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
        Object.defineProperty(navigator, 'injected', {get: () => 123});
        """
        
        page.add_init_script(stealth_script)

        # 如果有stealth.min.js文件，也尝试加载
        try:
            stealth_js_path = Path("stealth.min.js")
            if stealth_js_path.exists():
                with open(stealth_js_path, 'r', encoding='utf-8') as f:
                    stealth_js = f.read()
                page.add_init_script(stealth_js)
                log.info("已加载stealth.min.js文件")
        except Exception as e:
            log.info("未找到stealth.min.js文件，使用内置反检测脚本")
            
        log.info(f"已启用增强Stealth模式 (设备类型: {device_type or cls._default_device_type})")

    @classmethod
    def set_default_headers(cls, device_type: DeviceType = None):
        """设置默认请求头"""
        context = cls._get_context(device_type)
        
        is_mobile = device_type == DeviceType.MOBILE if device_type else False
        
        headers = {
            "sec-ch-ua": "\"Google Chrome\";v=\"135\", \"Not-A.Brand\";v=\"8\", \"Chromium\";v=\"135\"",
            "sec-ch-ua-mobile": "?1" if is_mobile else "?0",
            "sec-ch-ua-platform": "\"iOS\"" if is_mobile else "\"macOS\"",
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1" if is_mobile else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "accept-language": "zh-CN,zh;q=0.9",
            "referer": "https://www.zhipin.com/"
        }
        
        context.set_extra_http_headers(headers)
        log.info(f"已设置默认请求头 (设备类型: {device_type or cls._default_device_type})")

    @classmethod
    def get_page_object(cls, device_type: DeviceType = None) -> Page:
        """获取当前设备类型的Page对象"""
        return cls._get_page(device_type)

    @classmethod
    def set_cookie(cls, name: str, value: str, domain: str, path: str = "/",
                   expires: float = None, secure: bool = None, http_only: bool = None, 
                   device_type: DeviceType = None):
        """设置自定义Cookie"""
        cookie = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": path
        }
        
        if expires is not None:
            cookie["expires"] = expires
        if secure is not None:
            cookie["secure"] = secure
        if http_only is not None:
            cookie["httpOnly"] = http_only

        cookies = [cookie]
        cls._get_context(device_type).add_cookies(cookies)
        log.info(f"已设置Cookie: {name} (设备类型: {device_type or cls._default_device_type})")

    @classmethod
    def is_cookie_valid(cls, cookie_path: str) -> bool:
        """检查Cookie文件是否有效"""
        return Path(cookie_path).exists()

    @classmethod
    def find_element_with_message(cls, selector: str, message: str, device_type: DeviceType = None) -> Optional[Locator]:
        """带错误消息的元素查找"""
        try:
            locator = cls._get_page(device_type).locator(selector)
            # 检查元素是否存在
            if locator.count() > 0:
                return locator
            else:
                log.error(message)
                return None
        except Exception as e:
            log.error(f"{message}: {e}")
            return None
