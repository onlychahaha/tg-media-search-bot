# Telegram 媒体搜索机器人

这是一个用于Telegram群组的媒体搜索机器人，可以帮助用户在群组内搜索音频和视频文件。

## 功能

- 使用 `/f 关键词` 在群组内搜索媒体文件
- 使用 `/help` 获取使用帮助
- 分页显示搜索结果（每页10条）
- 文件名可直接点击跳转到原始消息
- 只有搜索发起者可以操作搜索结果
- 搜索结果10分钟后自动删除
- 当机器人加入新群组时，自动索引历史媒体文件

## 环境要求

- Python 3.9+
- MongoDB 4.0+
- Telegram API 密钥 (API ID 和 API HASH)
- Telegram Bot Token
- (可选) 代理服务器，如果需要通过代理连接Telegram
- Docker (用于运行MongoDB容器)

## 本地部署 (Ubuntu/WSL)

### 方案1: 直接在Ubuntu上运行，Docker运行MongoDB

#### 一键启动方式（推荐）

我们提供了便捷的启动和停止脚本：

```bash
# 赋予脚本执行权限
chmod +x start_local.sh stop_local.sh monitor_db.sh

# 启动机器人和MongoDB
./start_local.sh

# 停止机器人和MongoDB
./stop_local.sh

# 监控和查询MongoDB数据库
./monitor_db.sh
```

启动脚本会自动：
1. 检查Docker安装和运行状态
2. 检查并创建.env配置文件
3. 启动MongoDB容器（如果不存在会创建）
4. 安装所需的Python依赖
5. 启动机器人程序

数据库监控脚本提供了简便的方式连接到MongoDB容器，可以查询和管理数据。它会显示常用查询命令，方便开发调试。

#### WSL环境注意事项

如果在WSL环境中运行，请确保：
1. Docker Desktop for Windows已安装并启用了WSL集成
2. WSL中已安装Docker CLI (`sudo apt-get install docker.io`)
3. 如果启动脚本无法自动启动Docker服务，可能需要手动启动Docker Desktop

#### 手动步骤说明

1. 确保安装了Docker

```bash
# 如果没有安装Docker
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl enable --now docker
```

2. 运行MongoDB容器

```bash
# 创建数据存储目录
mkdir -p ~/mongodb_data

# 启动MongoDB容器
docker run -d --name mongodb \
  -p 27017:27017 \
  -v ~/mongodb_data:/data/db \
  --restart unless-stopped \
  mongo:4.4
```

3. 克隆仓库

```bash
git clone https://github.com/your-username/tg-media-search-bot.git
cd tg-media-search-bot
```

4. 安装依赖

```bash
# 安装Python依赖包
sudo apt-get install python3-pip
pip3 install -r requirements.txt
```

5. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 Telegram API 凭据和其他配置：
```
# MongoDB连接，指向本地Docker MongoDB容器
MONGODB_URI=mongodb://localhost:27017
```

6. 运行机器人

```bash
python3 -m app.main
```

### 方案2: 传统虚拟环境部署

1. 克隆仓库

```bash
git clone https://github.com/your-username/tg-media-search-bot.git
cd tg-media-search-bot
```

2. 创建虚拟环境并安装依赖 

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

3. 配置环境变量

复制 `.env.example` 文件为 `.env` 并填写必要信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 Telegram API 凭据和其他配置。

如果需要使用代理，请设置以下环境变量：
```
USE_PROXY=True
PROXY_TYPE=socks5  # 或 http
PROXY_HOST=127.0.0.1
PROXY_PORT=1080
PROXY_USERNAME=  # 如果代理需要认证
PROXY_PASSWORD=  # 如果代理需要认证
```

4. 运行机器人

```bash
python3 -m app.main
```

## Docker 完整部署

1. 克隆仓库

```bash
git clone https://github.com/your-username/tg-media-search-bot.git
cd tg-media-search-bot
```

2. 配置环境变量

复制 `.env.example` 文件为 `.env` 并填写必要信息：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 Telegram API 凭据和其他配置。

### Docker环境中使用代理

当在Docker环境中使用代理时，默认配置使用了`network_mode: "host"`，这使得容器可以直接访问宿主机的网络，包括代理服务。

如果您使用的是默认Docker网络模式（而不是host模式），需要调整以下设置：

1. 在`docker-compose.yml`中取消注释`extra_hosts`部分，注释掉`network_mode: "host"`

2. 修改`.env`文件中的代理配置：
```
PROXY_HOST=host.docker.internal  # 指向宿主机
# 或者使用宿主机的实际IP地址，而不是127.0.0.1
```

3. 同时修改MongoDB连接URI：
```
MONGODB_URI=mongodb://mongodb:27017  # 使用服务名而不是localhost
```

3. 使用 Docker Compose 启动服务

```bash
docker-compose up -d
```

## 获取 Telegram API 凭据

1. 访问 https://my.telegram.org/apps 并登录
2. 创建一个新的应用程序获取 API_ID 和 API_HASH
3. 使用 [@BotFather](https://t.me/BotFather) 创建一个新机器人获取 BOT_TOKEN

## 注意事项

- 此机器人需要使用 Telegram Client API 而不仅仅是 Bot API，因为需要访问群组历史消息
- 请确保机器人在群组中有足够的权限
- 避免在太多群组中使用同一个机器人实例，以防超出 Telegram API 限制
- 如果在网络受限的地区使用，请配置适当的代理

## 许可证

本项目采用 MIT 许可证
