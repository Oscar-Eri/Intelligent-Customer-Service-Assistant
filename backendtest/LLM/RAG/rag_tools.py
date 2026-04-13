"""
RAG 工具函数
提供知识库检索相关的工具,供 LangGraph 工作流调用
"""
from typing import List, Dict


def create_knowledge_retrieval_tool() -> Dict:
    """
    创建知识库检索工具定义(用于 Function Calling)
    
    Returns:
        工具定义字典,符合 OpenAI Function Calling 格式
        
    Example:
        >>> tool = create_knowledge_retrieval_tool()
        >>> print(tool["function"]["name"])  # "retrieve_knowledge"
    """
    return {
        "type": "function",
        "function": {
            "name": "retrieve_knowledge",
            "description": "从知识库中检索相关文件内容。可以检索特定文件、整个目录或所有文件。当用户询问产品规格、技术文档、业务资料等结构化知识时使用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "要检索的文件路径或目录路径列表。示例: ['Product-Line-A/SW-2100.md'] 检索单个文件, ['Product-Line-A/'] 检索整个目录, ['/'] 检索所有文件"
                    }
                },
                "required": ["file_paths"]
            }
        }
    }


async def retrieve_knowledge(file_paths: List[str]) -> str:
    """
    知识库检索工具函数
    
    Args:
        file_paths: 文件路径或目录路径列表
        
    Returns:
        检索到的文件内容字符串
        
    Example:
        >>> content = await retrieve_knowledge(["Product-Line-A/"])
        >>> print(content[:500])
    """
    from .knowledge_base import knowledge_base_manager
    
    print(f"🔍 检索知识库: {file_paths}")
    content = await knowledge_base_manager.retrieve_files(file_paths)
    print(f"✅ 检索完成,共 {len(content)} 字符")
    
    return content


def get_knowledge_summary() -> str:
    """
    获取知识库摘要(同步版本,用于构建系统提示词)
    
    Returns:
        知识库摘要文本
        
    Example:
        >>> summary = get_knowledge_summary()
        >>> print(summary[:200])
    """
    import asyncio
    from .knowledge_base import knowledge_base_manager
    
    # 由于这是同步函数,需要在新事件循环中运行
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环已在运行,创建新任务
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        pass
    
    loop = asyncio.new_event_loop()
    try:
        summary = loop.run_until_complete(knowledge_base_manager.get_file_summary())
        return summary
    finally:
        loop.close()


# 导出工具函数映射表(供 nodes.py 使用)
RAG_TOOLS = {
    'retrieve_knowledge': retrieve_knowledge
}

RAG_TOOLS_DESCRIPTION = """
## 可用工具

### retrieve_knowledge
用途: 从知识库检索文件内容
参数: {"file_paths": ["文件路径1", "目录路径/"]}
示例: 
  - 检索单个文件: ["Product-Line-A/SW-2100.md"]
  - 检索目录: ["Product-Line-A/"]
  - 检索全部: ["/"]
"""
