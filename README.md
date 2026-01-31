### 一个自动boss投递简历的工具

项目[getjobs](https://github.com/loks666/get_jobs) 的python版本，不太熟悉Java，python开发起来就更顺手一些, 方便做一些个性化的二次开发, 同时也是很棒的学习的机会。利用Deepseek把java转成了python，然后手工把代码调通，AI味道比较重。

* 目前对齐的版本是10.30号的版本。后面作者还更新了前端，有空研究一下。
* 手机端登录boss投简历暂时没调。移动端的职位推荐质量要比web端要好上太多了。
* 钉钉或者微信通知简历投递状态，没有支持

### 配置文件

配置文件在**config/config.yaml**， 各个配置项的含义很容易看懂

### 快速开始

测试环境是python3.10，其他的环境也可以试试

```bash
pip install -r requirements.txt  -i https://mirrors.aliyun.com/pypi/simple/
playwright install chromium
python3 main.py
```
### 关于找工作
首先boss直聘移动端的推荐只狼要高很好，优先在手机上投递。网页版本的投递工具作为补充。找工作经验就是多投，多面，多总结，量变终会产生质变。不要因为一时的被拒就否定自己，生死看淡不服就干！

### 禁止商业化
