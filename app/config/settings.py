import os
import re
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_env_var(var_name, default="", var_type=str):
    """
    获取环境变量并处理可能的注释
    
    :param var_name: 环境变量名
    :param default: 默认值
    :param var_type: 变量类型转换函数
    :return: 处理后的环境变量值
    """
    value = os.getenv(var_name, default)
    
    # 如果是字符串，去除可能的注释
    if isinstance(value, str):
        # 查找第一个未被引号包围的#号
        value = re.sub(r'(?<![\'"])#.*$', '', value).strip()
    
    # 类型转换
    if value == "":
        return default
    
    try:
        return var_type(value)
    except (ValueError, TypeError):
        return default

# Telegram 配置
API_ID = get_env_var("API_ID", "0", int)
API_HASH = get_env_var("API_HASH", "")
BOT_TOKEN = get_env_var("BOT_TOKEN", "")
SESSION_NAME = get_env_var("SESSION_NAME", "tg_media_search_bot")

# 代理配置
USE_PROXY = get_env_var("USE_PROXY", "False").lower() == "true"
PROXY_TYPE = get_env_var("PROXY_TYPE", "socks5")
PROXY_HOST = get_env_var("PROXY_HOST", "127.0.0.1")
PROXY_PORT = get_env_var("PROXY_PORT", "1080", int)
PROXY_USERNAME = get_env_var("PROXY_USERNAME", "")
PROXY_PASSWORD = get_env_var("PROXY_PASSWORD", "")

# MongoDB 配置
MONGODB_URI = get_env_var("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = get_env_var("DB_NAME", "tg_media_search")

# 应用配置
RESULTS_PER_PAGE = 10
AUTO_DELETE_TIMEOUT = 10 * 60  # 10分钟，单位：秒
