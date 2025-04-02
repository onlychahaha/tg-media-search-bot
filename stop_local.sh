#!/bin/bash

echo "========================================"
echo "Telegram媒体搜索机器人 - 本地停止脚本"
echo "========================================"

# 停止机器人进程
echo "停止机器人进程..."
pkill -f "python3 -m app.main" || echo "机器人进程未运行"

# 停止MongoDB容器
echo "停止MongoDB容器..."
MONGO_CONTAINER_ID=$(docker ps -q -f name=mongodb)
if [ -n "$MONGO_CONTAINER_ID" ]; then
    docker stop $MONGO_CONTAINER_ID
    echo "MongoDB容器已停止"
else
    echo "MongoDB容器未运行"
fi

echo "所有服务已停止" 