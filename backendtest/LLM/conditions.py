"""
条件函数
包含 LangGraph 对话引擎中的条件路由函数
"""


def should_use_human_review(state: dict) -> str:
    """
    条件路由函数
    决定是否需要人工审核
    
    Args:
        state: 当前对话状态
        
    Returns:
        str: 路由目标 ("human_review" 或 "llm_response")
    """
    if state.get('needs_human_review', False):
        return "human_review"
    else:
        return "llm_response"
