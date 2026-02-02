# Please install OpenAI SDK first: `pip3 install openai`
import os
from openai import OpenAI
from logger import log
from boss.boss_config import AIConfig, load_ai_config
from dataclasses import dataclass

@dataclass
class AiFilter:
    """AI过滤结果数据类"""
    result: bool
    message: str = ""
    ai_response: str = ""

class AIService:
    def __init__(self, ai_config: AIConfig) -> None:
        self.resume = "" 
        self.ai_config = ai_config
        md = ai_config.resume_md
        if os.path.exists(md) and md.endswith('.md'):
            self.resume = self.load_resume(md)
        else:
            log.error("Resume file not found or invalid format: %s", md)

    def load_resume(self, md:str) -> str:
        with open(md, 'r', encoding='utf-8') as file:
            markdown_content = file.read()
            return markdown_content
        return ""

    def chat(self, job_desc:str) -> str:
        # prompt = '''我在找工作，请根据我的简内容和岗位描述，判断是否匹配. 匹配得话还需要帮我生成简单的打招呼语, 30个字左右, 不要出现我的名字。不合适的话需要给出理由。\n '''
        # prompt += "简历信息:%s\n"
        # prompt += "岗位信息:%s\n"
        # prompt += '''返回json格式，除了json不要返回其他内容 。 例子1：{"match":true, "hi": "你好"}, 例子2: {"match":false, "hi":"经验不匹配"}''' 

        prompt = self.ai_config.prompt_template % (self.resume, job_desc)

        api_key = self.ai_config.api_key or os.environ.get('DEEPSEEK_API_KEY')
        base_url = self.ai_config.base_url or "https://api.deepseek.com"
        client = OpenAI( api_key=api_key, base_url=base_url)

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": f"{prompt}"},
            ],
            stream=False
        )

        log.info("AI response: %s", response.choices[0].message.content)
        return response.choices[0].message.content

if __name__ == "__main__":
    job_desc = '''1. 负BOSS直聘责AIGC内容kanzhun生成平台Web前端的来自BOSS直聘设计、开发与迭BOSS直聘代优化。
2. 构建复杂的管理后台界面，实现包括但不限于：
3. 提示词（Prompt）编辑器：支持多模态、分段、带权重的复杂提示词输入与管理。
4. AI模型参数控制面板：直观配置多种AI大模型（如SDXL、Midjourney、SVD、LLM等）的深度参数（采样器、步数、CFG scale、种子等）。
5. 实现任务队列与实时状态更新系统，清晰展示图片、视频生成、处理的进度和结果。
6. 开发多媒体素材管理模块，支持生成结果的预览、筛选、批量操作与合成（如图片拼接为视频）。
7. 与后端工程师紧密协作，定义高效的API接口，处理大规模文件（图片、视频）的上传、下载与流式传输。
8. 持续优化前端性能、响应速度和用户体验，确保在大规模数据和高并发操作下的应用流畅度。
岗位要求
1. 对AIGC内容生成行业充满兴趣与热情。
2. 精通 React 或 Vue3 现代前端框架及其生态（如 Redux, Vuex, React Router, Vite等），并具备大型单页应用（SPA）开发经验。
3. 深刻理解JavaScript（ES6+）、TypeScript、HTML5、CSS3等前端核心技术。
4. 具备良好的前端工程化能力，熟悉Webpack、Vite等构建工具，有模块化、组件化开发经验。
5. 出色的UI/UX实现能力，能独立将设计稿转化为高保真、交互流畅的Web界面。熟悉Ant Design、Element-UI等主流UI框架。
6. 熟练掌握Vibe Coding技能
7. 具备良好的沟通能力、团队协作精神和解决问题的能力。
8. 本科及以上学历，计算机相关专业，5年以上前端开发经验。
加分项
1. 有AIGC相关项目（如Stable Diffusion, Midjourney, ChatGPT等应用）开发经验者优先。
2. 有复杂后台管理系统、富文本编辑器、数据可视化项目经验者优先。
3. 熟悉Canvas、WebGL、FFmpeg.wasm等音视频处理相关技术者优先。
4. 了解WebSocket、SSE等技术，有实时应用开发经验者优先。
5. 对用户体验和交互设计有深刻理解，对技术有激情，乐于探索和学习新技术。
'''
    ai_config = load_ai_config()
    bot = AIService(ai_config)
    bot.chat(job_desc)
