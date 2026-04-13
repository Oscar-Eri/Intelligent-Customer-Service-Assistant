"""
状态定义
包含 LangGraph 对话引擎中使用的各种状态类
"""
from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """对话状态"""
    messages: Annotated[List[BaseMessage], operator.add]
    user_input: str
    ai_response: str
    needs_human_review: bool
    sentiment_result: dict  # 情感分析结果
    intent_result: dict  # 意图识别结果
    keywords_result: dict  # 关键词提取结果
    entities_result: dict  # 实体抽取结果
    rag_retrieved_content: str  # RAG 检索到的知识库内容
    rag_used: bool  # 是否使用了 RAG 检索
