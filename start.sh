#!/bin/bash

# AI会议助手 - 快速启动脚本
# 作者: Augment Agent
# 日期: 2025-06-26

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 AI会议助手 - 快速启动${NC}"
echo "=================================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装，请先安装Docker${NC}"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose未安装，请先安装Docker Compose${NC}"
    exit 1
fi

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker未运行，请启动Docker后重试${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker环境检查通过${NC}"

# 选择配置文件
if [ -f "docker-compose.prod.yml" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
    echo -e "${BLUE}📋 使用生产环境配置: ${COMPOSE_FILE}${NC}"
elif [ -f "docker-compose.yml" ]; then
    COMPOSE_FILE="docker-compose.yml"
    echo -e "${BLUE}📋 使用默认配置: ${COMPOSE_FILE}${NC}"
else
    echo -e "${RED}❌ 未找到docker-compose配置文件${NC}"
    exit 1
fi

# 拉取最新镜像
echo -e "${BLUE}📥 拉取最新镜像...${NC}"
docker-compose -f ${COMPOSE_FILE} pull

# 启动服务
echo -e "${BLUE}🔧 启动服务...${NC}"
docker-compose -f ${COMPOSE_FILE} up -d

# 等待服务启动
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo -e "${BLUE}🔍 检查服务状态...${NC}"
docker-compose -f ${COMPOSE_FILE} ps

# 健康检查
echo -e "${BLUE}🏥 执行健康检查...${NC}"
for i in {1..10}; do
    if curl -f http://localhost:8080/api/status > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 服务启动成功！${NC}"
        break
    else
        echo -e "${YELLOW}⏳ 等待服务启动... (${i}/10)${NC}"
        sleep 5
    fi
    
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ 服务启动失败，请检查日志${NC}"
        echo -e "${YELLOW}查看日志命令: docker-compose -f ${COMPOSE_FILE} logs meetaudio-web${NC}"
        exit 1
    fi
done

# 显示访问信息
echo ""
echo "=================================================="
echo -e "${GREEN}🎉 AI会议助手启动成功！${NC}"
echo ""
echo -e "${YELLOW}📱 访问地址:${NC}"
echo "  本地访问: http://localhost:8080"
echo "  网络访问: http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo -e "${YELLOW}🔧 管理命令:${NC}"
echo "  查看状态: docker-compose -f ${COMPOSE_FILE} ps"
echo "  查看日志: docker-compose -f ${COMPOSE_FILE} logs -f meetaudio-web"
echo "  停止服务: docker-compose -f ${COMPOSE_FILE} down"
echo "  重启服务: docker-compose -f ${COMPOSE_FILE} restart"
echo ""
echo -e "${YELLOW}⚙️ 首次使用:${NC}"
echo "  1. 访问系统设置页面"
echo "  2. 配置豆包AI API Key"
echo "  3. 配置字节跳动ASR API Key"
echo "  4. 配置火山引擎TOS存储"
echo ""
echo "=================================================="
