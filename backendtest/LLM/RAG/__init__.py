"""
RAG (Retrieval-Augmented Generation) 模块
提供知识库检索增强生成功能

模块结构:
- knowledge_base.py: 知识库管理器,负责文件检索
- llm_provider.py: LLM Provider 抽象层,统一 API 调用
- generate_summary.py: 知识库摘要生成器
- rag_tools.py: RAG 相关工具函数(供 LangGraph 使用)

使用示例:
    from .RAG import knowledge_base_manager
    content = await knowledge_base_manager.retrieve_files(["Product-Line-A/"])
"""

from .knowledge_base import KnowledgeBaseManager, knowledge_base_manager
from .llm_provider import UnifiedLLMProvider, create_qwen_provider

__all__ = [
    'KnowledgeBaseManager',
    'knowledge_base_manager',
    'UnifiedLLMProvider',
    'create_qwen_provider'
]
