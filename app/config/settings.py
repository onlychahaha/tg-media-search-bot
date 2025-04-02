import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Telegram 配置
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_NAME = os.getenv("SESSION_NAME", "tg_media_search_bot")

# 代理配置
USE_PROXY = os.getenv("USE_PROXY", "False").lower() == "true"
PROXY_TYPE = os.getenv("PROXY_TYPE", "socks5")  # socks5 或 http
PROXY_HOST = os.getenv("PROXY_HOST", "127.0.0.1")
PROXY_PORT = int(os.getenv("PROXY_PORT", "1080"))
PROXY_USERNAME = os.getenv("PROXY_USERNAME", "")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "")

# MongoDB 配置
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "tg_media_search")

# 应用配置
RESULTS_PER_PAGE = 10
AUTO_DELETE_TIMEOUT = 10 * 60  # 10分钟，单位：秒
