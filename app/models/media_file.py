from pymongo import MongoClient, ASCENDING, TEXT
from datetime import datetime
from app.config.settings import MONGODB_URI, DB_NAME

class MediaFileModel:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db.media_files
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """创建必要的索引"""
        # 文件名文本索引
        self.collection.create_index([("file_name", TEXT)])
        # 消息ID和群组ID的复合索引
        self.collection.create_index([("message_id", ASCENDING), ("chat_id", ASCENDING)], unique=True)
        # 时间戳索引，用于排序
        self.collection.create_index([("timestamp", ASCENDING)])
    
    def add_media_file(self, file_data):
        """添加新的媒体文件记录"""
        file_data["indexed_at"] = datetime.now()
        
        # 检查是否已存在相同记录
        existing = self.collection.find_one({
            "message_id": file_data["message_id"],
            "chat_id": file_data["chat_id"]
        })
        
        if existing:
            return None
        
        result = self.collection.insert_one(file_data)
        return result.inserted_id
    
    def search_media_files(self, keyword, chat_id, skip=0, limit=10):
        """搜索媒体文件"""
        query = {
            "$text": {"$search": keyword},
            "chat_id": chat_id
        }
        
        # 按时间戳降序排列（最新的优先）
        cursor = self.collection.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        
        return list(cursor)
    
    def count_search_results(self, keyword, chat_id):
        """计算搜索结果总数"""
        query = {
            "$text": {"$search": keyword},
            "chat_id": chat_id
        }
        return self.collection.count_documents(query)
    
    def get_media_file_by_id(self, file_id):
        """通过ID查找媒体文件"""
        return self.collection.find_one({"_id": file_id})
    
    def close(self):
        """关闭数据库连接"""
        self.client.close()
