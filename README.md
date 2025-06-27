# 火山引擎语音识别API Python客户端

基于火山引擎大模型录音文件识别API的Python客户端库，支持异步音频转文本处理。

## 功能特性

- 🎯 简单易用的API封装
- 🔄 自动重试机制
- ⚡ 异步任务处理
- 🛡️ 完善的错误处理
- 📝 详细的日志记录
- 🔧 灵活的配置管理

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 配置API密钥

创建 `.env` 文件：

```env
BYTEDANCE_APP_KEY=your_app_key
BYTEDANCE_ACCESS_KEY=your_access_key
```

### 2. 基本使用

```python
from meetaudio import ByteDanceASRClient

# 初始化客户端
client = ByteDanceASRClient()

# 提交音频文件进行识别
task_id = client.submit_audio("http://example.com/audio.mp3")

# 查询识别结果
result = client.get_result(task_id)
print(result.text)
```

### 3. 命令行工具

```bash
# 识别音频文件
python -m meetaudio.cli transcribe --url "http://example.com/audio.mp3"

# 查询任务状态
python -m meetaudio.cli query --task-id "your-task-id"
```

## API文档

### ByteDanceASRClient

主要的客户端类，提供语音识别功能。

#### 方法

- `submit_audio(url, **options)` - 提交音频文件进行识别
- `get_result(task_id)` - 查询识别结果
- `wait_for_result(task_id, timeout=300)` - 等待识别完成并返回结果

#### 配置选项

- `enable_itn` - 启用文本规范化（默认: True）
- `enable_punc` - 启用标点符号（默认: False）
- `enable_ddc` - 启用语义顺滑（默认: False）
- `enable_speaker_info` - 启用说话人分离（默认: False）
- `show_utterances` - 输出详细分句信息（默认: False）

## 错误处理

客户端会自动处理常见错误：

- 网络超时自动重试
- API限流自动等待
- 无效参数提前验证
- 详细的错误信息

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black meetaudio/
flake8 meetaudio/
```

## 许可证

MIT License
