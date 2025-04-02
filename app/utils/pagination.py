from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.config.settings import RESULTS_PER_PAGE

class Pagination:
    def __init__(self, total_results, current_page=1, per_page=RESULTS_PER_PAGE):
        """
        初始化分页器
        
        :param total_results: 总结果数
        :param current_page: 当前页码，从1开始
        :param per_page: 每页显示的结果数
        """
        self.total_results = total_results
        self.current_page = max(1, current_page)
        self.per_page = per_page
        self.total_pages = (total_results + per_page - 1) // per_page
    
    def get_skip(self):
        """获取需要跳过的结果数量"""
        return (self.current_page - 1) * self.per_page
    
    def get_pagination_keyboard(self, search_query, page_callback_data_format):
        """
        生成分页键盘
        
        :param search_query: 搜索查询，用于构建回调数据
        :param page_callback_data_format: 页码回调数据格式，如 "page:{query}:{page}"
        :return: InlineKeyboardMarkup 对象
        """
        buttons = []
        
        # 上一页按钮
        if self.current_page > 1:
            prev_page_data = page_callback_data_format.format(
                query=search_query, page=self.current_page - 1
            )
            buttons.append(InlineKeyboardButton("⬅️ 上一页", callback_data=prev_page_data))
        
        # 当前页信息
        page_info = f"📄 {self.current_page}/{self.total_pages}"
        buttons.append(InlineKeyboardButton(page_info, callback_data="noop"))
        
        # 下一页按钮
        if self.current_page < self.total_pages:
            next_page_data = page_callback_data_format.format(
                query=search_query, page=self.current_page + 1
            )
            buttons.append(InlineKeyboardButton("下一页 ➡️", callback_data=next_page_data))
        
        # 关闭按钮
        buttons.append(InlineKeyboardButton("❌ 关闭", callback_data="close"))
        
        # 构建行，每行最多放3个按钮
        keyboard = []
        for i in range(0, len(buttons), 3):
            row = buttons[i:min(i+3, len(buttons))]
            keyboard.append(row)
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def format_results(results, chat_id):
        """
        格式化搜索结果
        
        :param results: 搜索结果列表
        :param chat_id: 群组ID
        :return: 格式化后的结果文本
        """
        if not results:
            return "没有找到匹配的媒体文件。"
        
        formatted_text = "🔍 **搜索结果**:\n\n"
        
        for i, result in enumerate(results):
            file_type_emoji = "🎵" if result["media_type"] == "audio" else "🎬"
            file_name = result["file_name"]
            message_id = result["message_id"]
            
            # 创建文件名超链接，点击可跳转到原消息
            link = f"https://t.me/c/{str(chat_id).replace('-100', '')}/{message_id}"
            line = f"{i+1}. {file_type_emoji} [{file_name}]({link})\n"
            
            formatted_text += line
        
        return formatted_text
