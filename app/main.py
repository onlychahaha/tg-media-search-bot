import os
import logging
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ChatType
from app.config.settings import (
    API_ID, API_HASH, BOT_TOKEN, SESSION_NAME,
    USE_PROXY, PROXY_TYPE, PROXY_HOST, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD
)
from app.handlers.search_handler import SearchHandler
from app.utils.indexing import MediaIndexer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MediaSearchBot:
    def __init__(self):
        """初始化机器人"""
        # 创建Pyrogram客户端
        client_kwargs = {
            "name": SESSION_NAME,
            "api_id": API_ID,
            "api_hash": API_HASH,
            "bot_token": BOT_TOKEN
        }
        
        # 如果启用了代理，添加代理配置
        if USE_PROXY:
            proxy = {
                "scheme": PROXY_TYPE,
                "hostname": PROXY_HOST,
                "port": PROXY_PORT
            }
            
            # 如果有用户名和密码，添加到代理配置中
            if PROXY_USERNAME and PROXY_PASSWORD:
                proxy["username"] = PROXY_USERNAME
                proxy["password"] = PROXY_PASSWORD
                
            client_kwargs["proxy"] = proxy
            logger.info(f"使用{PROXY_TYPE}代理: {PROXY_HOST}:{PROXY_PORT}")
        
        self.app = Client(**client_kwargs)
        
        # 初始化媒体索引器
        self.indexer = MediaIndexer(self.app)
        
        # 初始化搜索处理器
        self.search_handler = SearchHandler(self.app)
        
        # 注册其他事件处理器
        self._register_handlers()
    
    def _register_handlers(self):
        """注册事件处理器"""
        # 新消息处理器，用于实时索引新媒体文件
        self.app.add_handler(
            MessageHandler(
                self._handle_new_message,
                filters.media & filters.group
            )
        )
        
        # 加入新群组处理器
        self.app.add_handler(
            MessageHandler(
                self._handle_new_chat,
                filters.new_chat_members & filters.group
            )
        )
    
    async def _handle_new_message(self, client, message):
        """处理新消息，将媒体文件添加到索引"""
        await self.indexer.process_new_message(message)
    
    async def _handle_new_chat(self, client, message):
        """处理加入新群组的事件"""
        # 检查是否是机器人被添加
        added_me = False
        for member in message.new_chat_members:
            if member.is_self:
                added_me = True
                break
        
        if not added_me:
            return
        
        chat_id = message.chat.id
        chat_title = message.chat.title
        
        logger.info(f"机器人被添加到新群组: {chat_title} ({chat_id})")
        
        # 发送欢迎消息
        welcome_text = (
            f"👋 你好！我是媒体搜索机器人。\n\n"
            f"我可以帮助你搜索群组内的音频和视频文件。\n"
            f"使用 `/f 关键词` 来搜索文件。\n\n"
            f"正在为此群组建立媒体索引，请稍候..."
        )
        welcome_msg = await message.reply(welcome_text)
        
        try:
            # 启动索引过程
            count = await self.indexer.index_chat_history(chat_id)
            
            # 更新欢迎消息
            await welcome_msg.edit_text(
                f"✅ 索引完成！已为群组 '{chat_title}' 索引了 {count} 个媒体文件。\n\n"
                f"使用 `/f 关键词` 来搜索文件。"
            )
        except Exception as e:
            logger.error(f"为群组 {chat_id} 建立索引时出错: {str(e)}")
            await welcome_msg.edit_text(
                f"❌ 索引过程出错。请确保机器人拥有足够的权限。\n\n"
                f"仍然可以使用 `/f 关键词` 来搜索已索引的文件。"
            )
    
    async def start(self):
        """启动机器人"""
        await self.app.start()
        me = await self.app.get_me()
        logger.info(f"机器人已启动: @{me.username}")
        
        # 保持机器人运行
        await idle()
    
    async def stop(self):
        """停止机器人"""
        await self.app.stop()
        logger.info("机器人已停止")

async def main():
    """主函数"""
    bot = MediaSearchBot()
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("接收到退出信号")
    finally:
        await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
