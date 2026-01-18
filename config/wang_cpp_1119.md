<h3 align="center">王佳伟</h3>
### 基本信息
<table style="border: none; border-collapse: collapse; margin: 0 auto; width:100%">
<tr style="border: none;">
<td style="border: none; text-align: left;">🏠杭州</td>
<td style="border: none; text-align: center; ">📞13161014851</td>
<td style="border: none; text-align: center; ">📧1216451203@qq.com</td>
<td style="border: none; text-align: right; ;">👨‍💻C++开发</td>
</tr>
</table>
### 个人经历
<table style="border: none; border-collapse: collapse; margin: 0 auto; width:100%">
<tr style="border: none;">
<td style="border: none; text-align: left; ">2023.12-2023.08</td>
<td style="border: none; text-align: left; ">蚂蚁金服</td>
<td style="border: none; text-align: left; ">数字人工程</td>
<td style="border: none; text-align: right; ">研发工程师</td>
</tr>
<tr style="border: none;">
<td style="border: none; text-align: left; ">2019.12-2023.12</td>
<td style="border: none; text-align: left; ">百度</td>
<td style="border: none; text-align: left; ">语音技术部</td>
<td style="border: none; text-align: right; ">研发工程师</td>
</tr>
<tr style="border: none;">
<td style="border: none; text-align: left; ">2017.07-2019.12</td>
<td style="border: none; text-align: left; ">北京华大九天股份有限公司</td>
<td style="border: none; text-align: left; ">研发二部</td>
<td style="border: none; text-align: right; ">研发工程师</td>
</tr>
<tr style="border: none;">
<td style="border: none; text-align: left; ">2014.09-2017.06</td>
<td style="border: none; text-align: left; ">中国科学院大学电子学研究所</td>
<td style="border: none; text-align: left; ">电子设计自动化</td>
<td style="border: none; text-align: right; ">硕士</td>
</tr>
<tr style="border: none;">
<td style="border: none; text-align: left; ">2010.09-2014.07</td>
<td style="border: none; text-align: left; ">山东大学</td>
<td style="border: none; text-align: left; ">集成电路设计</td>
<td style="border: none; text-align: right; ">本科</td>
</table>



### 项目经历

<h4 align="center">数字人多模态实时交互Linux服务 | 蚂蚁金服</h4>

为实现数字人与用户的低延迟、多模态（音/视/图/文）实时对话、需要构建一个高性能，高可用Linux中枢服务，解决数据传输、AI能力集成与链路耗时三大挑战。主要职责：

**架构设计：** 设计了 HTTP + WebRTC 的混合架构，利用HTTP完成信令握手，利用WebRTC实现端到服务端的高效、双向多媒体数据传输。

**AI能力集成：** 设计并实现**AI客户端资源池**，通过连接复用与统一生命周期管理，杜绝了内存泄漏，保障了服务长稳运行。

**性能优化：** 在用户说话时即异步请求LLM，语音结束即可获取LLM响应，同时缓存语音合成TTS，大幅削减等待时间。

**智能理解增强：**为弥补LLM视觉能力不足，**自建图片向量检索服务**，实现多模态信息的精准对齐与高质量Prompt构建。

**收益**：打造的系统稳定运行，每秒在线人数25。智能客服端到端平均响应时间**优化至2秒内**，关键路径**累计降低延迟800ms**，体验提升显著。技术方案具备强扩展性，已成功复制到**医疗、文博**等跨领域合作项目中。

<h4 align="center">数字人移动端渲染 | 蚂蚁金服</h4>

云端GPU渲染成本高昂，严重制约数字人产品的规模化发展。为此，作为技术主力，承接了端侧CPU低成本推理引擎的自主研发项目，旨将核心渲染引擎从云端GPU迁移到端侧CPU。主要职责：

**核心算法重构：** 将Python算法（口型推理、Opencv克隆等）用 **C++重写并编译为WebAssembly**，实现计算密集型任务在Web环境的原生性能。

**并行架构设计：** 设计 **WebWorker多进程架构**，实现渲染任务并行化，解决单线程阻塞问题。

**可观测性建设：** 设计**进程间通信日志方案**，为运行在虚拟机内的渲染引擎打造了状态可观测能力。

**兼容性优化：** 通过优化编译降低WASM产物体积、重写基础库、剔除Thread/Mutex/Atomic等高级特性，实现对中低端机型的广泛适配。

**收益：** 端侧WebAssembly引擎性能相比JavaScript**提升超10倍**，用户体验达到“实时”级别。实现中高端机**>90%机型覆盖**。技术方案成功上线智能客服项目，**直接节省70%+云端成本**。

<h4 align="center">数字人全链路监控与日志查询系统 | 蚂蚁金服</h4>

为解决数字人多技术栈（Java/C++/Python）服务下，问题定位困难、缺乏统一观测视角的痛点。独立负责从0到1设计并落地一套以TraceID为核心的全链路信息查询系统。主要职责：

**标准化与设计：**定义并推行了一套的**关键日志格式规范**，确保关键服务日志可被SQL查询与分析。

**基础设施构建：** 通过定制**基础Docker镜像**，自动化完成了机器指标与业务日志的采集和上报。

**可视化与告警：** 基于Grafana对接SLS数据源，构建可视化仪表盘；并配置告警规则，将异常指标通过钉钉群实时通知。

**收益:**  成功实现**“一Trace通查”**，问题排查效率提升**90%以上**。形成的值班机制，确保了线上问题能被快速响应与处理。实现了全链路日志的长期存储，为后续的用户行为分析与系统优化提供了**数据基础**。

<h4 align="center">语音识别智能纠错 | 百度语音</h4>

车载语音特定Badcase（如“挂R档”）引发严重客诉，车厂要求快速Case级修复，且不能影响大盘指标。作为核心设计与开发者，构建一个高效、精准的实时纠错系统。主要职责：

**构建训练集合：** 搭建**Badcase收集平台**，自动化拉取音频与标注，构建定向优化语料。

**设计纠错引擎：** 创新性地提出 “大盘模型 + 专家模型”的双层解码架构。

- **触发层：** 基于Badcase统计，构建了支持热加载的正则表达式二次解码池，实时判断识别结果可信度。
- **纠错层：** 针对命中池子的低置信结果，调用专门为Badcase训练的Tiny专家模型进行二次识别，以专家结果为准。

**实现快速响应：**  确保整个纠错链路支持**热更新**，无需重启服务即可生效新规则与模型，实现无缝干预

**收益：**将目标Badcase集的识别准确率**提升至95%+**，并具备秒级别快速干预能力。该技术方案成为**核心竞标优势**，直接转化为商业合作，**赢得了多家车企项目**。

<h4 align="center">神经网络语言模型集成 | 百度语音</h4>

传统N-gram语言模型内存占用高、上下文建模能力弱，成为识别准确率进一步提升的瓶颈。负责将神经网络语言模型高效集成到实时语音识别解码器中，并解决其带来的性能挑战。主要职责：

**模型集成：** 使用 **ONNX Runtime** 集成NNLM，完成C++侧的高效调用与打分。

**解码器改造：** 重新设计得分融合策略，在路径扩展时，对每个Token进行**声学分与NNLM语言分的加权计算**。

**内存控制：**  实现 **Beam Search** 剪枝策略，在保证精度的前提下，严格控制并行路径数量，确保服务内存稳定。

**收益：**模型上线后，**长文本识别准确率获得10%的相对提升**。完成算力基础设施升级T4->A10，单机最大并发量从**50提升到200**。技术方案稳定高效，未引发线上故障。

### 开源项目

* [kokoro-onnx](https://github.com/wjwever/kokoro-onnx) 高还原度语音合成系统，自动纠正中英文、数字、符号混杂输入，CPU机器可运行，可合成超长文本，多音色可选。
* [sensevoice-onnx](https://github.com/wjwever/sensevoice-onnx) 低成本语音识别系统，支持中、英、日、粤语识别， 识别结果自动标点、正则。
* [duix.ai](https://github.com/wjwever/duix.ai.core) 你的web桌面爱豆数字人，CPU机器本地可运行，实时对话端到端延时低至2s。

### 专业技能
* 熟悉 C/C++、Python、GCC、GDB、VIM 开发环境，熟悉 Linux 服务端HTTP、WebSocket、RPC协议以及编程
* 掌握 Redis、MySql 等服务端开发工具; 掌握 WeNet、OnnxRuntime 等开源工具
