### 一个自动boss投递简历的工具

其实是项目[getjobs](https://github.com/loks666/get_jobs) 的python版本，不太熟悉Java，python开发起来就更顺手一些，所以利用Deepseek把java转成了python，然后手工把代码调通，整体看起来AI味道会重一些。

* 目前对齐的版本是10.30号的版本。后面我看到作者有新的提交，暂时没有同步，这个版本平时用来投投简历已经够用了。
* 目前只支持web端登录，代码里面的mobile手机端登录暂时没调通。移动端的职位推荐质量要比web端要好上太多了。后续研究下怎么加上.
* 钉钉或者微信通知简历投递状态，还没有支持

### 配置文件

配置文件在**data/config.yaml**， 各个配置项的含义很容易看懂

### 快速开始

测试环境是python3.10，其他的环境也可以试试

```bash
pip install -r requirements.txt  -i https://mirrors.aliyun.com/pypi/simple/
playwright install chromium
python3 main.py
```

