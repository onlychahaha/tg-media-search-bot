import re
import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.models.media_file import MediaFileModel
from app.utils.pagination import Pagination
from app.config.settings import RESULTS_PER_PAGE, AUTO_DELETE_TIMEOUT

logger = logging.getLogger(__name__)

# 存储活跃搜索的字典 {message_id: {"user_id": user_id, "query": query, "chat_id": chat_id}}
active_searches = {}

class SearchHandler:
    def __init__(self, bot):
        """
        初始化搜索处理器
        
        :param bot: Pyrogram机器人客户端实例
        """
        self.bot = bot
        self.db = MediaFileModel()
        self._register_handlers()
    
    def _register_handlers(self):
        """注册消息和回调处理器"""
        # 注册/f命令处理器
        self.bot.on_message(filters.command("f") & filters.group)(self.handle_search_command)
        
        # 注册/help命令处理器
        self.bot.on_message(filters.command("help"))(self.handle_help_command)
        
        # 注册分页回调处理器
        self.bot.on_callback_query(filters.regex(r"^page:(.+):(\d+)$"))(self.handle_page_callback)
        
        # 注册关闭回调处理器
        self.bot.on_callback_query(filters.regex(r"^close$"))(self.handle_close_callback)
    
    async def handle_help_command(self, client, message):
        """处理/help命令"""
        help_text = (
            "📚 **媒体搜索机器人使用说明**\n\n"
            "这是一个帮助你在群组内搜索音频和视频文件的机器人。\n\n"
            "**主要命令**：\n"
            "• `/f 关键词` - 搜索包含指定关键词的媒体文件\n"
            "• `/help` - 显示此帮助信息\n"
            "• `/index` - 【仅管理员】索引群组历史媒体文件\n\n"
            "**使用方法**：\n"
            "1. 首先，确保机器人拥有管理员权限\n"
            "2. 确保用户账号已加入此群组\n"
            "3. 群组管理员使用 `/index` 命令索引历史媒体文件\n"
            "4. 在群组中发送 `/f 关键词` 来搜索媒体\n"
            "5. 搜索结果将显示为分页列表，每页10条记录\n"
            "6. 点击文件名可直接跳转到原始消息\n"
            "7. 只有搜索发起者可以操作分页按钮\n"
            "8. 搜索结果将在10分钟后自动删除\n\n"
            "**提示**：\n"
            "• 搜索是基于文件名进行的\n"
            "• 机器人会自动索引新上传的媒体文件\n"
            "• 历史媒体文件需要通过 `/index` 命令手动索引\n"
            "• 若没有搜索到结果，可能是文件名中不包含您搜索的关键词，或者历史文件尚未索引\n"
        )
        
        await message.reply(help_text, quote=True)
    
    async def handle_search_command(self, client, message):
        """处理/f搜索命令"""
        try:
            # 提取搜索关键词
            command_parts = message.text.split(maxsplit=1)
            if len(command_parts) < 2:
                await message.reply("请提供搜索关键词，例如: /f 音乐", quote=True)
                return
            
            search_query = command_parts[1].strip()
            
            # 获取搜索结果
            total_results = self.db.count_search_results(search_query, message.chat.id)
            
            if total_results == 0:
                await message.reply(f"没有找到包含关键词 '{search_query}' 的媒体文件。", quote=True)
                return
            
            # 初始化分页器
            paginator = Pagination(total_results)
            skip = paginator.get_skip()
            
            # 获取第一页结果
            results = self.db.search_media_files(search_query, message.chat.id, skip, RESULTS_PER_PAGE)
            
            # 格式化结果
            result_text = Pagination.format_results(results, message.chat.id)
            
            # 创建分页键盘
            keyboard = paginator.get_pagination_keyboard(search_query, "page:{query}:{page}")
            
            # 发送结果
            reply = await message.reply(
                result_text,
                quote=True,
                reply_markup=keyboard,
                disable_web_page_preview=True,
                parse_mode="markdown"
            )
            
            # 记录活跃搜索
            active_searches[reply.id] = {
                "user_id": message.from_user.id,
                "query": search_query,
                "chat_id": message.chat.id
            }
            
            # 设置自动删除计时器
            asyncio.create_task(self._schedule_delete(reply.id, message.chat.id, AUTO_DELETE_TIMEOUT))
            
        except Exception as e:
            logger.error(f"处理搜索命令时出错: {str(e)}")
            await message.reply("搜索时发生错误，请稍后再试。", quote=True)
    
    async def handle_page_callback(self, client, callback_query):
        """处理分页回调"""
        try:
            # 解析回调数据
            match = re.match(r"^page:(.+):(\d+)$", callback_query.data)
            search_query = match.group(1)
            page = int(match.group(2))
            message_id = callback_query.message.id
            
            # 检查是否是原始搜索者
            if message_id not in active_searches:
                await callback_query.answer("此搜索已过期。", show_alert=True)
                return
                
            if callback_query.from_user.id != active_searches[message_id]["user_id"]:
                await callback_query.answer("只有搜索发起者可以操作分页。", show_alert=True)
                return
            
            chat_id = active_searches[message_id]["chat_id"]
            
            # 获取结果总数
            total_results = self.db.count_search_results(search_query, chat_id)
            
            # 初始化分页器
            paginator = Pagination(total_results, page)
            skip = paginator.get_skip()
            
            # 获取当前页结果
            results = self.db.search_media_files(search_query, chat_id, skip, RESULTS_PER_PAGE)
            
            # 格式化结果
            result_text = Pagination.format_results(results, chat_id)
            
            # 创建分页键盘
            keyboard = paginator.get_pagination_keyboard(search_query, "page:{query}:{page}")
            
            # 更新消息
            await callback_query.message.edit_text(
                result_text,
                reply_markup=keyboard,
                disable_web_page_preview=True,
                parse_mode="markdown"
            )
            
            await callback_query.answer()
            
        except Exception as e:
            logger.error(f"处理分页回调时出错: {str(e)}")
            await callback_query.answer("操作失败，请重试。", show_alert=True)
    
    async def handle_close_callback(self, client, callback_query):
        """处理关闭回调"""
        try:
            message_id = callback_query.message.id
            
            # 检查是否是原始搜索者
            if message_id not in active_searches:
                await callback_query.answer("此搜索已过期。", show_alert=True)
                return
                
            if callback_query.from_user.id != active_searches[message_id]["user_id"]:
                await callback_query.answer("只有搜索发起者可以关闭搜索。", show_alert=True)
                return
            
            # 删除搜索结果
            await callback_query.message.delete()
            # 清理活跃搜索记录
            if message_id in active_searches:
                del active_searches[message_id]
                
            await callback_query.answer("搜索已关闭。")
            
        except Exception as e:
            logger.error(f"处理关闭回调时出错: {str(e)}")
            await callback_query.answer("关闭失败，请重试。", show_alert=True)
    
    async def _schedule_delete(self, message_id, chat_id, timeout):
        """
        安排自动删除消息
        
        :param message_id: 消息ID
        :param chat_id: 聊天ID
        :param timeout: 超时时间（秒）
        """
        await asyncio.sleep(timeout)
        
        # 如果消息ID仍在活跃搜索中，则删除
        if message_id in active_searches:
            try:
                await self.bot.delete_messages(chat_id, message_id)
                del active_searches[message_id]
                logger.info(f"自动删除了消息ID: {message_id}")
            except Exception as e:
                logger.error(f"自动删除消息时出错: {str(e)}")
