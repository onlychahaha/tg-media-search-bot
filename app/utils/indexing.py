from pyrogram import Client
from pyrogram.enums import MessageMediaType
from datetime import datetime
import asyncio
import logging
from app.models.media_file import MediaFileModel

logger = logging.getLogger(__name__)

class MediaIndexer:
    def __init__(self, client):
        """
        初始化媒体索引器
        
        :param client: Pyrogram客户端实例
        """
        self.client = client
        self.db = MediaFileModel()
    
    async def index_chat_history(self, chat_id):
        """
        索引指定群组的历史媒体消息
        
        :param chat_id: 群组ID
        :return: 索引的媒体文件数量
        """
        logger.info(f"开始索引群组 {chat_id} 的历史媒体文件")
        count = 0
        
        try:
            async for message in self.client.get_chat_history(chat_id):
                if await self._process_message(message):
                    count += 1
                    
                # 每处理100条消息输出一次日志
                if count > 0 and count % 100 == 0:
                    logger.info(f"已索引 {count} 条媒体文件")
                    
                # 避免请求过于频繁
                await asyncio.sleep(0.05)
                
        except Exception as e:
            logger.error(f"索引群组 {chat_id} 历史时出错: {str(e)}")
        
        logger.info(f"群组 {chat_id} 历史索引完成，共索引 {count} 条媒体文件")
        return count
    
    async def _process_message(self, message):
        """
        处理单条消息，如果是音频或视频则添加到数据库
        
        :param message: Pyrogram消息对象
        :return: 是否成功处理了媒体文件
        """
        if not message.media:
            return False
            
        media_type = None
        file_name = None
        file_id = None
        file_size = None
        duration = None
        
        # 检查消息是否包含音频或视频
        if message.audio:
            media_type = "audio"
            media = message.audio
            file_name = media.file_name or f"audio_{message.id}.mp3"
            file_id = media.file_id
            file_size = media.file_size
            duration = media.duration
        elif message.video:
            media_type = "video"
            media = message.video
            file_name = media.file_name or f"video_{message.id}.mp4"
            file_id = media.file_id
            file_size = media.file_size
            duration = media.duration
        elif message.document and message.document.mime_type:
            mime = message.document.mime_type.lower()
            if mime.startswith("audio/"):
                media_type = "audio"
                media = message.document
                file_name = media.file_name or f"audio_{message.id}"
                file_id = media.file_id
                file_size = media.file_size
            elif mime.startswith("video/"):
                media_type = "video"
                media = message.document
                file_name = media.file_name or f"video_{message.id}"
                file_id = media.file_id
                file_size = media.file_size
        
        if not media_type:
            return False
            
        # 准备文件数据
        file_data = {
            "file_id": file_id,
            "file_name": file_name,
            "message_id": message.id,
            "chat_id": message.chat.id,
            "sender_id": message.from_user.id if message.from_user else 0,
            "timestamp": datetime.utcfromtimestamp(message.date),
            "media_type": media_type,
            "file_size": file_size,
            "duration": duration
        }
        
        # 添加到数据库
        try:
            result = self.db.add_media_file(file_data)
            return result is not None
        except Exception as e:
            logger.error(f"添加媒体文件到数据库时出错: {str(e)}")
            return False
    
    async def process_new_message(self, message):
        """
        处理新消息，如果是媒体文件则添加到索引
        
        :param message: Pyrogram消息对象
        :return: 是否成功处理了媒体文件
        """
        return await self._process_message(message)
