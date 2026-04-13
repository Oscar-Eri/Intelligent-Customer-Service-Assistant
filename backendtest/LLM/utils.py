"""
工具函数
提供 LangGraph 聊天服务的辅助函数
"""
from .service import LangGraphChatService


def create_langgraph_service() -> LangGraphChatService:
    """
    创建 LangGraph 聊天服务实例
    
    Returns:
        LangGraphChatService 实例
    """
    return LangGraphChatService()
