"""
Memory 模块 - 记忆管理
提供对话历史的存储、检索和管理功能
包括短期记忆（MemoryManager）、知识库（KnowledgeBase）和 ContextAtlas 集成
"""
from .memory_manager import MemoryManager, create_memory_manager

# ContextAtlas 适配器（可选，如果文件存在则导入）
try:
    from .contextatlas_adapter import ContextAtlasAdapter, create_contextatlas_adapter
    __all__ = [
        'MemoryManager',
        'create_memory_manager',
    ]
except ImportError:
    __all__ = [
        'MemoryManager',
        'create_memory_manager',
    ]
