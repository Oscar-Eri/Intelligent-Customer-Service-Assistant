"""
MCP (Model Context Protocol) 消息协议定义
定义智能体间的通信格式,确保高内聚低耦合
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class MessageType(str, Enum):
    """消息类型枚举"""
    REQUEST = "request"           # 请求消息
    RESPONSE = "response"         # 响应消息
    EVENT = "event"               # 事件通知
    ERROR = "error"               # 错误消息


class AgentRole(str, Enum):
    """智能体角色枚举"""
    COORDINATOR = "coordinator"           # 协调者(主控)
    RAG_AGENT = "rag_agent"               # RAG 检索智能体
    SENTIMENT_AGENT = "sentiment_agent"   # 情感分析智能体
    INTENT_AGENT = "intent_agent"         # 意图识别智能体
    MEMORY_AGENT = "memory_agent"         # 记忆管理智能体
    LLM_RESPONSE_AGENT = "llm_response_agent"  # LLM 响应智能体


class MessagePriority(int, Enum):
    """消息优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class MCPMessage(BaseModel):
    """
    MCP 标准消息格式
    
    所有智能体间通信都使用此格式,确保:
    - 统一的消息结构
    - 完整的追踪信息
    - 灵活的扩展能力
    """
    
    # 消息标识
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # 消息类型和优先级
    message_type: MessageType = MessageType.REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    
    # 发送者和接收者
    sender: AgentRole
    receiver: Optional[AgentRole] = None  # None 表示广播
    
    # 消息内容
    action: str = Field(..., description="动作名称,如 'analyze_sentiment', 'retrieve_knowledge'")
    payload: Dict[str, Any] = Field(default_factory=dict, description="消息负载数据")
    
    # 上下文信息
    conversation_id: Optional[str] = None  # 对话ID,用于关联同一对话的消息
    parent_message_id: Optional[str] = None  # 父消息ID,用于追踪消息链
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MCPResponse(BaseModel):
    """
    MCP 标准响应格式
    """
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    message_id: str  # 原始请求的 message_id


# ==================== 常用消息模板 ====================

def create_rag_request(user_input: str, conversation_id: str = None) -> MCPMessage:
    """创建 RAG 检索请求"""
    return MCPMessage(
        sender=AgentRole.COORDINATOR,
        receiver=AgentRole.RAG_AGENT,
        action="retrieve_knowledge",
        payload={
            "user_input": user_input,
            "max_results": 5
        },
        conversation_id=conversation_id
    )


def create_sentiment_request(text: str, conversation_id: str = None) -> MCPMessage:
    """创建情感分析请求"""
    return MCPMessage(
        sender=AgentRole.COORDINATOR,
        receiver=AgentRole.SENTIMENT_AGENT,
        action="analyze_sentiment",
        payload={
            "text": text
        },
        conversation_id=conversation_id
    )


def create_intent_request(text: str, conversation_id: str = None) -> MCPMessage:
    """创建意图识别请求"""
    return MCPMessage(
        sender=AgentRole.COORDINATOR,
        receiver=AgentRole.INTENT_AGENT,
        action="analyze_intent",
        payload={
            "text": text
        },
        conversation_id=conversation_id
    )


def create_memory_save_request(messages: List[Dict], conversation_id: str = None) -> MCPMessage:
    """创建记忆保存请求"""
    return MCPMessage(
        sender=AgentRole.COORDINATOR,
        receiver=AgentRole.MEMORY_AGENT,
        action="save_memory",
        payload={
            "messages": messages
        },
        conversation_id=conversation_id
    )


def create_llm_response_request(
    user_input: str,
    context: Dict[str, Any],
    conversation_id: str = None
) -> MCPMessage:
    """创建 LLM 响应生成请求"""
    return MCPMessage(
        sender=AgentRole.COORDINATOR,
        receiver=AgentRole.LLM_RESPONSE_AGENT,
        action="generate_response",
        payload={
            "user_input": user_input,
            "context": context  # 包含情感、意图、RAG 结果等
        },
        conversation_id=conversation_id
    )


# ==================== 示例用法 ====================

if __name__ == "__main__":
    # 示例: 创建一条 RAG 检索请求
    msg = create_rag_request(
        user_input="SW-2100智能手表的电池续航是多少?",
        conversation_id="conv_123"
    )
    
    print("MCP 消息示例:")
    print(msg.json(indent=2, ensure_ascii=False))
