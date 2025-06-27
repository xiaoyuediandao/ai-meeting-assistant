# 使用Ubuntu作为基础镜像
FROM ubuntu:22.04

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DEBIAN_FRONTEND=noninteractive

# 安装Python和系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    gcc \
    g++ \
    curl \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .
COPY web_demo/requirements-web.txt ./web_demo/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r web_demo/requirements-web.txt

# 复制项目文件
COPY meetaudio/ ./meetaudio/
COPY web_demo/ ./web_demo/
COPY setup.py .
COPY README.md .

# 安装meetaudio包
RUN pip install -e .

# 创建必要的目录
RUN mkdir -p /app/web_demo/uploads \
    && mkdir -p /app/web_demo/task_data \
    && mkdir -p /app/logs

# 设置权限
RUN chmod -R 755 /app/web_demo

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/status || exit 1

# 切换到web_demo目录
WORKDIR /app/web_demo

# 启动命令
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
