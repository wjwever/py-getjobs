### 一个自动boss投递简历的工具

其实是项目[getjobs](https://github.com/loks666/get_jobs) 的python版本，不太熟悉Java，python开发起来就更顺手一些，所以利用Deepseek把java转成了python，然后手工把代码调通，整体看起来AI味道会重一些。

* 目前对齐的版本是10.30号的版本。后面我看到作者有新的提交，暂时没有同步，这个版本平时用来投投简历已经够用了。
* 目前只支持web端登录，代码里面的mobile手机端登录暂时没调通。不过移动端的简历推荐质量要比web端要号上太多了。
* 钉钉发送通知消息，这块没有加上。

### 配置文件

配置文件在**data/config.yaml**， 各个配置项的含义很容易看懂

### 快速开始

测试环境是python3.10，其他的环境也可以试试

```bash
pip install -r requirements.txt  -i https://mirrors.aliyun.com/pypi/simple/
python3 main.py
```

