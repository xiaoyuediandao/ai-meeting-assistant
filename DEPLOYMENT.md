# AI会议助手 - 部署指南

## 📋 概述

本文档介绍如何在生产环境中部署AI会议助手系统。

## 🚀 快速部署

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 服务器内存: 至少2GB
- 磁盘空间: 至少10GB

### 2. 下载部署文件

```bash
# 下载docker-compose配置文件
wget https://raw.githubusercontent.com/your-repo/meetaudio/main/docker-compose.prod.yml

# 或者手动创建docker-compose.yml文件
```

### 3. 启动服务

```bash
# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f meetaudio-web
```

### 4. 访问应用

- 应用地址: http://your-server-ip:8080
- 健康检查: http://your-server-ip:8080/api/status

## ⚙️ 配置说明

### 系统配置

首次启动后，需要在系统设置中配置以下信息：

#### AI配置
- **豆包AI API Key**: 您的豆包AI API密钥
- **模型名称**: 您的模型
- **API地址**: https://ark.cn-beijing.volces.com/api/v3
- **超时时间**: 300秒

#### ASR配置
- **App Key**: 您的字节跳动ASR App Key
- **Access Key**: 您的字节跳动ASR Access Key
- **模型**: bigmodel
- **超时时间**: 1800秒

#### 存储配置
- **TOS Access Key**: 您的火山引擎TOS Access Key
- **TOS Secret Key**: 您的火山引擎TOS Secret Key
- **存储桶**: meetaudio (或您的存储桶名称)
- **区域**: cn-beijing
- **最大文件大小**: 500MB

## 🔧 高级配置

### 环境变量

可以通过环境变量覆盖默认配置：

```yaml
environment:
  - FLASK_ENV=production
  - MAX_CONTENT_LENGTH=524288000  # 500MB
  - UPLOAD_TIMEOUT=300
  - AI_TIMEOUT=300
```

### 资源限制

默认资源配置：
- 内存限制: 2GB
- CPU限制: 1核
- 内存预留: 512MB
- CPU预留: 0.5核

### 数据持久化

系统使用Docker卷进行数据持久化：
- `meetaudio-uploads`: 上传文件存储
- `meetaudio-tasks`: 任务数据存储
- `meetaudio-logs`: 日志文件存储
- `meetaudio-config`: 配置文件存储

## 🛠️ 运维操作

### 查看日志
```bash
docker-compose logs -f meetaudio-web
```

### 重启服务
```bash
docker-compose restart meetaudio-web
```

### 更新镜像
```bash
docker-compose pull
docker-compose up -d
```

### 备份数据
```bash
# 备份配置
docker cp meetaudio-web:/app/web_demo/config ./backup/config

# 备份数据卷
docker run --rm -v meetaudio-config:/data -v $(pwd):/backup alpine tar czf /backup/config-backup.tar.gz -C /data .
```

## 🔒 安全建议

1. **防火墙配置**: 只开放必要的端口(8080)
2. **HTTPS配置**: 建议使用Nginx反向代理配置SSL
3. **定期备份**: 定期备份配置和重要数据
4. **监控告警**: 配置服务监控和告警

## 📊 监控

### 健康检查
系统内置健康检查端点: `/api/status`

### 日志监控
重要日志位置:
- 应用日志: `/app/logs/`
- 容器日志: `docker logs meetaudio-web`

## 🆘 故障排除

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用
   - 检查Docker服务状态
   - 查看容器日志

2. **配置无法保存**
   - 检查数据卷权限
   - 确认配置格式正确

3. **API调用失败**
   - 检查网络连接
   - 验证API密钥
   - 查看API调用日志

### 联系支持

如遇到问题，请提供以下信息：
- 系统版本信息
- 错误日志
- 配置信息(脱敏后)

## 📝 更新日志

- v1.0.0: 初始版本发布
- 支持豆包AI会议纪要生成
- 支持字节跳动ASR语音识别
- 支持火山引擎TOS云存储
