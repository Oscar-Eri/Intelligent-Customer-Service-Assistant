"""
LangGraph 智能对话引擎 - 主集成文件
负责集成所有子模块，提供统一的导入接口
"""

# 从各个子模块导入组件
from .models import AgentState
from .nodes import (
    process_input_node,
    llm_response_node,
    review_decision_node,
    human_review_node,
    sentiment_analysis_node  # 新增情感分析节点
)
from .conditions import should_use_human_review
from .workflow import build_chat_workflow
from .service import LangGraphChatService
from .utils import create_langgraph_service


# ==================== 导出公共接口 ====================

__all__ = [
    # 状态
    'AgentState',
    
    # 节点
    'process_input_node',
    'llm_response_node',
    'review_decision_node',
    'human_review_node',
    'sentiment_analysis_node',  # 新增情感分析节点
    
    # 条件函数
    'should_use_human_review',
    
    # 工作流
    'build_chat_workflow',
    
    # 服务
    'LangGraphChatService',
    
    # 工具函数
    'create_langgraph_service',
]


# ==================== 快速使用示例 ====================

if __name__ == "__main__":
    import asyncio
    
    async def test_chat():
        # 使用工具函数创建服务
        service = create_langgraph_service()
        
        print("=" * 50)
        print("LangGraph 聊天测试（输入 'quit' 退出）")
        print("=" * 50)
        
        while True:
            user_input = input("\n👤 你：").strip()
            
            if user_input.lower() == 'quit':
                break
            
            if not user_input:
                continue
            
            response = await service.chat(user_input)
            print(f"🤖 AI: {response}")
    
    asyncio.run(test_chat())
