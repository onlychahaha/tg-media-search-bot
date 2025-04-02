# Telegram 媒体搜索机器人

这是一个用于Telegram群组的媒体搜索机器人，可以帮助用户在群组内搜索音频和视频文件。

## 功能

- 使用 `/f 关键词` 在群组内搜索媒体文件
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

## 本地开发部署

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
python -m app.main
```

## Docker 部署

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
