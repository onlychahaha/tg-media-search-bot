import os
import logging
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ChatType
from pyrogram.types import Chat, User, ChatMember
from app.config.settings import (
    API_ID, API_HASH, BOT_TOKEN, SESSION_NAME,
    USE_PROXY, PROXY_TYPE, PROXY_HOST, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD
)
from app.handlers.search_handler import SearchHandler
from app.utils.indexing import MediaIndexer
import platform

# 配置日志 - 只保留重要日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MediaSearchBot:
    def __init__(self):
        """初始化媒体搜索机器人 - 使用双客户端架构"""
        logger.info("初始化媒体搜索机器人")
        
        # 检查必要环境变量
        if not API_ID or not API_HASH or not BOT_TOKEN:
            raise ValueError("缺少必要的API凭据，请检查.env文件")
        
        # 配置代理（如果启用）
        proxy = None
        if USE_PROXY:
            proxy = {
                "scheme": PROXY_TYPE,
                "hostname": PROXY_HOST,
                "port": PROXY_PORT
            }
            
            if PROXY_USERNAME and PROXY_PASSWORD:
                proxy["username"] = PROXY_USERNAME
                proxy["password"] = PROXY_PASSWORD
                
            logger.info(f"已配置{PROXY_TYPE}代理")
        
        # 设备标识参数 - 非常重要
        # 这些参数确保客户端被识别为独立设备，不会干扰其他设备的会话
        # 即使在程序退出后重新启动，也会使用相同标识
        device_model = "TgMediaSearchBot"  # 固定标识，避免随机命名
        system_version = platform.system()  # 系统类型
        app_version = "1.0.0"              # 应用版本
        
        # 检查会话文件
        user_session_path = f"{SESSION_NAME}_user.session"
        if not os.path.isfile(user_session_path):
            logger.warning(f"未找到用户会话文件: {user_session_path}")
            logger.warning("请先运行 'python3 auth_user.py' 创建会话文件")
        
        # 创建用户客户端 - 用于索引历史消息
        # 关键: 保持与auth_user.py中相同的设备标识参数，确保认为是同一设备
        self.user = Client(
            name=SESSION_NAME + "_user",  # 与auth_user.py中相同
            workdir="./",                 # 确保会话文件路径一致 
            api_id=API_ID,
            api_hash=API_HASH,
            proxy=proxy,
            device_model=device_model,    # 与用户认证保持一致
            system_version=system_version,
            app_version=app_version,
            in_memory=False,              # 文件存储会话
            no_updates=True,              # 不接收更新，只用于API调用
            allow_flooded=True            # 允许在短时间内发送大量请求（适用于索引功能）
        )
        
        # 创建机器人客户端 - 用于处理搜索命令
        bot_device_model = f"{device_model}_Bot"  # 区分机器人和用户客户端
        self.bot = Client(
            name=SESSION_NAME + "_bot",
            workdir="./",
            api_id=API_ID,
            api_hash=API_HASH,
            proxy=proxy,
            device_model=bot_device_model,  # 与用户客户端区分
            system_version=system_version,
            app_version=app_version,
            bot_token=BOT_TOKEN
        )
        
        # 初始化媒体索引器和搜索处理器
        self.indexer = MediaIndexer(self.user)
        self.search_handler = SearchHandler(self.bot)
        
        # 注册事件处理器
        self._register_handlers()
    
    def _register_handlers(self):
        """注册事件处理器"""
        # 用户客户端 - 处理新媒体文件
        try:
            self.user.add_handler(
                MessageHandler(
                    self._handle_new_message,
                    filters.media & filters.group
                )
            )
        except Exception as e:
            logger.error(f"注册用户客户端处理器失败: {e}")
        
        # 机器人客户端 - 处理命令
        try:
            # 加入新群组处理
            self.bot.add_handler(
                MessageHandler(
                    self._handle_new_chat,
                    filters.new_chat_members & filters.group
                )
            )
            
            # 索引命令处理
            self.bot.add_handler(
                MessageHandler(
                    self._handle_index_command,
                    filters.command("index") & filters.group
                )
            )
        except Exception as e:
            logger.error(f"注册机器人处理器失败: {e}")
            raise
    
    async def _handle_new_message(self, client, message):
        """处理新消息，将媒体文件添加到索引"""
        await self.indexer.process_new_message(message)
    
    async def _handle_index_command(self, client, message):
        """处理索引命令，开始检索群组历史媒体文件"""
        # 检查命令发送者是否有管理员权限
        is_admin = False
        user_id = message.from_user.id
        
        try:
            # 获取用户在群组中的详细信息
            chat = message.chat
            user = await chat.get_member(user_id)
            
            # 检查用户状态 - 使用正确的状态值: owner(群主)和administrator(管理员)
            if hasattr(user, 'status'):
                if isinstance(user.status, str):
                    is_admin = user.status in ["owner", "administrator"]
                elif hasattr(user.status, 'value'):
                    status_value = user.status.value
                    is_admin = status_value in ["owner", "administrator", "creator", 1, 2]
            
            # 对于Pyrogram API，使用ChatMember类的特殊检查
            if hasattr(user, '__class__'):
                class_name = str(user.__class__)
                owner_check = any(owner_term in class_name for owner_term in ['ChatMemberOwner', 'ChannelParticipantCreator'])
                admin_check = any(admin_term in class_name for admin_term in ['ChatMemberAdministrator', 'ChannelParticipantAdmin'])
                is_admin = is_admin or owner_check or admin_check
                
        except Exception as e:
            logger.error(f"检查用户权限时出错: {str(e)}")
        
        if not is_admin:
            await message.reply("⚠️ 只有群组管理员可以使用索引命令。", quote=True)
            return
        
        chat_id = message.chat.id
        chat_title = message.chat.title
        
        # 检查用户客户端是否已经登录
        if not self.user.is_connected:
            await message.reply(
                "⚠️ 用户客户端未连接，无法执行索引。请确保已正确配置用户账号。", 
                quote=True
            )
            return
        
        # 检查用户客户端是否有权限访问该群组
        try:
            # 使用用户客户端获取群组信息来验证访问权限
            chat = await self.user.get_chat(chat_id)
            logger.info(f"开始索引群组: {chat.title}")
        except Exception as e:
            logger.error(f"用户客户端无法访问群组: {str(e)}")
            await message.reply(
                "⚠️ 索引失败：用户客户端无法访问此群组。请确保用户账号已加入此群组。", 
                quote=True
            )
            return
                
        # 发送开始索引消息
        indexing_msg = await message.reply(
            f"🔍 开始索引群组 '{chat_title}' 的历史媒体文件...\n"
            f"这可能需要一些时间，取决于群组大小和历史消息数量。", 
            quote=True
        )
        
        try:
            # 启动索引过程
            count = await self.indexer.index_chat_history(chat_id)
            
            # 更新索引完成消息
            await indexing_msg.edit_text(
                f"✅ 索引完成！已为群组 '{chat_title}' 索引了 {count} 个媒体文件。\n\n"
                f"使用 `/f 关键词` 来搜索文件。\n"
                f"使用 `/help` 获取更多帮助。"
            )
        except Exception as e:
            logger.error(f"索引失败: {str(e)}")
            await indexing_msg.edit_text(
                f"❌ 索引过程出错: {str(e)}\n\n"
                f"此错误可能是因为用户客户端权限不足或其他限制导致。"
            )
    
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
        
        logger.info(f"机器人被添加到群组: {chat_title}")
        
        # 发送欢迎消息
        welcome_text = (
            f"👋 你好！我是媒体搜索机器人。\n\n"
            f"我可以帮助你搜索群组内的音频和视频文件。\n"
            f"使用 `/f 关键词` 来搜索文件。\n"
            f"使用 `/help` 获取更多帮助。\n\n"
            f"⚠️ 重要提示：请授予我管理员权限，并确保用户账号已加入此群组，然后使用 `/index` 命令开始索引群组历史媒体文件。"
        )
        await message.reply(welcome_text)
    
    async def start(self):
        """启动机器人 - 包括用户客户端和机器人客户端"""
        # 先启动用户客户端
        user_connected = False
        
        try:
            logger.info("正在启动用户客户端...")
            # 重要：这里的start()不会要求重新登录
            # 如果会话文件有效，它会自动恢复会话而不是请求手机号和验证码
            # 这不是重复登录，而是利用auth_user.py已经创建的会话凭证
            await self.user.start()
            user_connected = True
            user_info = await self.user.get_me()
            logger.info(f"用户客户端已启动: {user_info.first_name}")
        except Exception as e:
            logger.error(f"启动用户客户端失败: {str(e)}")
            logger.info("继续启动机器人客户端...")
        
        # 然后启动机器人客户端
        try:
            logger.info("正在启动机器人客户端...")
            await self.bot.start()
            bot_info = await self.bot.get_me()
            logger.info(f"机器人客户端已启动: @{bot_info.username}")
            
            # 打印启动信息
            print(f"\n{'='*30}")
            print(f"媒体搜索机器人已启动!")
            print(f"机器人: @{bot_info.username}")
            if user_connected:
                print(f"历史消息索引功能已启用")
            else:
                print(f"警告: 历史消息索引功能未启用")
            print(f"{'='*30}\n")
            
            # 保持机器人运行
            await idle()
            
        except Exception as e:
            logger.error(f"启动机器人客户端失败: {str(e)}")
            raise
    
    async def stop(self):
        """停止机器人 - 只关闭当前连接，不会影响其他设备会话"""
        try:
            # 关闭机器人客户端
            await self.bot.stop()
            logger.info("机器人客户端已停止")
            
            # 关闭用户客户端
            # 注意: stop()方法只会关闭当前连接，不会撤销会话凭证
            # 这确保下次启动时可以无缝恢复会话，也不会影响其他设备
            await self.user.stop()
            logger.info("用户客户端已停止")
        except Exception as e:
            logger.error(f"停止客户端时出错: {str(e)}")

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
