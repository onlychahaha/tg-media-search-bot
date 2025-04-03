#!/bin/bash
set -e

echo "========================================"
echo "Telegram媒体搜索机器人 - 启动脚本"
echo "========================================"

# 检查Docker是否已安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装。请先安装Docker。"
    exit 1
fi

# 检查Docker服务是否运行
docker info > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "启动Docker服务..."
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

# 检查用户会话文件是否存在
SESSION_NAME=$(grep "SESSION_NAME" .env | cut -d "=" -f2)
SESSION_NAME=${SESSION_NAME:-tg_media_search_bot}  # 默认值
USER_SESSION="${SESSION_NAME}_user.session"

if [ ! -f "$USER_SESSION" ]; then
    echo "⚠️ 未找到用户会话文件: $USER_SESSION"
    echo "请先运行用户认证脚本生成会话文件，以便访问群组历史消息"
    echo "运行命令: python3 auth_user.py"
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
        mkdir -p ~/mongodb_data
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
python3 -m app.main