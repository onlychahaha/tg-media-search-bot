#!/bin/bash
set -e

echo "========================================"
echo "Telegram媒体搜索机器人 - 本地启动脚本"
echo "========================================"

# 检查Docker是否已安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装。请先安装Docker。"
    echo "可以使用命令: sudo apt-get install docker.io"
    exit 1
fi

# 检查Docker服务是否运行（适配WSL环境）
docker info > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "启动Docker服务..."
    # 尝试多种可能的启动方式
    sudo service docker start || sudo /etc/init.d/docker start || echo "无法自动启动Docker服务，请手动启动"
    
    # 再次检查
    docker info > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "错误: Docker服务未能启动。请手动启动Docker服务后再运行此脚本。"
        exit 1
    fi
fi

# 检查.env文件是否存在
if [ ! -f .env ]; then
    echo "创建.env文件..."
    cp .env.example .env
    echo "请编辑.env文件，填写Telegram API凭据"
    exit 1
fi

# 检查MongoDB容器是否已存在
MONGO_CONTAINER_ID=$(docker ps -q -f name=mongodb)
if [ -z "$MONGO_CONTAINER_ID" ]; then
    MONGO_CONTAINER_ID=$(docker ps -aq -f name=mongodb)
    if [ -n "$MONGO_CONTAINER_ID" ]; then
        echo "启动已存在的MongoDB容器..."
        docker start $MONGO_CONTAINER_ID
    else
        echo "创建并启动MongoDB容器..."
        # 创建数据目录
        mkdir -p ~/mongodb_data
        
        # 启动MongoDB容器
        docker run -d --name mongodb \
            -p 27017:27017 \
            -v ~/mongodb_data:/data/db \
            --restart unless-stopped \
            mongo:4.4
    fi
else
    echo "MongoDB容器已在运行中..."
fi

# 安装必要的Python依赖
echo "检查Python依赖..."
pip3 install -r requirements.txt

# 启动机器人
echo "启动Telegram媒体搜索机器人..."
#python3 -m app.main 
python3 -m debugpy --listen 5678 --wait-for-client main.py