#!/bin/bash

echo "========================================"
echo "Telegram媒体搜索机器人 - MongoDB监控工具"
echo "========================================"

# 检查MongoDB容器是否运行
MONGO_CONTAINER_ID=$(docker ps -q -f name=mongodb)
if [ -z "$MONGO_CONTAINER_ID" ]; then
    echo "错误: MongoDB容器未运行"
    echo "请先运行 ./start_local.sh 启动MongoDB容器"
    exit 1
fi

# 打印MongoDB容器信息
echo "MongoDB容器信息:"
docker ps -f name=mongodb

# 获取数据库名称
if [ -f .env ]; then
    DB_NAME=$(grep "DB_NAME" .env | cut -d "=" -f2)
    if [ -z "$DB_NAME" ]; then
        DB_NAME="tg_media_search"
    fi
else
    DB_NAME="tg_media_search"
fi

echo "连接到数据库: $DB_NAME"
echo "输入'exit'退出"
echo "========================================"

# 连接到MongoDB shell
docker exec -it $MONGO_CONTAINER_ID mongosh "$DB_NAME"

# 连接后显示有用的查询提示
echo "========================================"
echo "常用查询命令:"
echo "1. 查看所有集合: show collections"
echo "2. 查看媒体文件数量: db.media_files.count()"
echo "3. 查看最新10条媒体文件: db.media_files.find().sort({timestamp:-1}).limit(10)"
echo "4. 按关键词搜索: db.media_files.find({file_name: /关键词/})"
echo "5. 按特定群组查询: db.media_files.find({chat_id: 群组ID})"
echo "========================================" 