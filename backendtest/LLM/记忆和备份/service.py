"""    
服务类
LangGraph 聊天服务的封装
"""
from typing import List, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from ..workflow import build_chat_workflow


class LangGraphChatService:
    """
    LangGraph 聊天服务
    封装工作流，提供简单接口
    """
    
    def __init__(self):
        self.app = build_chat_workflow()
        self.conversation_history: List[BaseMessage] = []
    
    async def chat(self, user_message: str) -> str:
        """
        处理用户消息并返回 AI 回复
        
        Args:
            user_message: 用户输入
            
        Returns:
            AI 回复内容
        """
        # 添加用户消息到历史
        self.conversation_history.append(HumanMessage(content=user_message))
        
        # 运行工作流
        result = await self.app.ainvoke({
            "messages": self.conversation_history.copy(),
            "user_input": user_message,
            "ai_response": "",
            "needs_human_review": False
        })
        
        # 保存 AI 回复到历史
        ai_response = result["ai_response"]
        self.conversation_history.append(AIMessage(content=ai_response))
        
        return ai_response
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
    
    def get_history(self) -> List[BaseMessage]:
        """获取对话历史"""
        return self.conversation_history.copy()
    
    async def chat_stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        流式处理用户消息并生成 AI 回复
        
        Args:
            user_message: 用户输入
            
        Yields:
            AI 回复的文本片段
        """
        from langchain_openai import ChatOpenAI
        from ..config import qwen_base_url, qwen_api_key
        
        # 添加用户消息到历史
        self.conversation_history.append(HumanMessage(content=user_message))
        
        # 创建 LLM 实例（启用流式）
        llm = ChatOpenAI(
            model="qwen-plus",
            base_url=qwen_base_url,
            api_key=qwen_api_key,
            temperature=0.7,
            streaming=True,  # 启用流式输出
        )
        
        # 流式调用 LLM
        full_response = ""
        try:
            async for chunk in llm.astream(self.conversation_history):
                if chunk.content:
                    full_response += chunk.content
                    yield chunk.content  # 实时返回文本片段
            
            # 保存完整回复到历史
            self.conversation_history.append(AIMessage(content=full_response))
            
        except Exception as e:
            error_msg = f"抱歉，发生错误：{str(e)}"
            yield error_msg
