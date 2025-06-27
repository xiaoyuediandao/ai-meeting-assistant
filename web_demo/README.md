# 火山引擎语音识别Web演示

这是一个基于火山引擎语音识别API的Web演示界面，提供直观的用户界面来展示语音转文字功能。

## 功能特性

- 🎨 **现代化UI设计** - 参考原图设计，采用渐变色彩和卡片式布局
- 📁 **多种输入方式** - 支持文件上传和URL输入
- 🎛️ **灵活配置选项** - 文本规范化、标点符号、说话人分离等
- ⚡ **实时状态更新** - 进度条显示和状态反馈
- 📊 **详细结果展示** - 识别文本、分句信息、统计数据
- 📱 **响应式设计** - 适配桌面和移动设备

## 快速开始

### 1. 安装依赖

```bash
# 在项目根目录
pip install -r requirements.txt
```

### 2. 配置API密钥

```bash
# 方法一：环境变量
export BYTEDANCE_APP_KEY=your_app_key
export BYTEDANCE_ACCESS_KEY=your_access_key

# 方法二：.env文件（推荐）
cp ../.env.example ../.env
# 编辑 .env 文件填入您的密钥
```

### 3. 启动服务

```bash
# 方法一：使用启动脚本（推荐）
python3 start_demo.py

# 方法二：直接启动Flask
python3 app.py
```

### 4. 访问界面

打开浏览器访问：http://localhost:5000

## 界面说明

### 主要区域

1. **标题区域** - 显示服务名称和描述
2. **上传区域** - 支持拖拽上传和点击选择文件
3. **URL输入** - 输入在线音频文件地址
4. **配置选项** - 识别参数设置
5. **状态显示** - 处理进度和任务信息
6. **结果展示** - 识别文本和详细信息

### 配置选项

- **文本规范化** - 将数字、时间等转换为标准格式
- **标点符号** - 自动添加标点符号
- **说话人分离** - 区分不同说话人（最多10人）
- **详细分句** - 显示时间戳和分句信息

### 支持格式

- **音频格式**: MP3、WAV、OGG、RAW
- **文件大小**: 最大16MB
- **输入方式**: 本地文件上传、在线URL

## API接口

### POST /api/submit
提交识别任务

```json
{
  "audio_url": "https://example.com/audio.mp3",
  "format": "mp3",
  "config": {
    "enable_itn": true,
    "enable_punc": false,
    "enable_speaker": false,
    "show_utterances": true
  }
}
```

### GET /api/query/{task_id}
查询任务状态

### GET /api/wait/{task_id}
等待任务完成

### GET /api/status
获取服务状态

## 演示模式

如果没有配置API密钥，系统会自动进入演示模式：

- 使用模拟数据展示界面功能
- 模拟识别过程和结果
- 适合功能演示和界面测试

## 部署说明

### 开发环境
```bash
python3 app.py
# 访问 http://localhost:5000
```

### 生产环境
```bash
# 使用Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 使用uWSGI
pip install uwsgi
uwsgi --http :5000 --wsgi-file app.py --callable app
```

### Docker部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

## 自定义配置

### 修改端口
```python
# 在 app.py 最后一行修改
app.run(debug=True, host='0.0.0.0', port=8080)
```

### 修改样式
编辑 `style.css` 文件自定义界面样式

### 添加功能
在 `script.js` 中添加新的交互功能

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查环境变量设置
   - 确认密钥格式正确

2. **网络连接问题**
   - 检查音频URL是否可访问
   - 确认防火墙设置

3. **文件格式不支持**
   - 确认音频格式在支持列表中
   - 检查文件是否损坏

4. **服务启动失败**
   - 检查端口是否被占用
   - 确认依赖是否正确安装

### 日志查看

服务运行时会在控制台输出详细日志，包括：
- 请求处理信息
- API调用状态
- 错误详情

## 技术栈

- **前端**: HTML5, CSS3, JavaScript (ES6+)
- **后端**: Python Flask
- **API**: 火山引擎语音识别服务
- **样式**: 自定义CSS，Font Awesome图标
- **部署**: 支持多种部署方式

## 许可证

MIT License
