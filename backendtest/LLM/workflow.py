"""
工作流构建
负责构建 LangGraph 对话工作流
"""
from langgraph.graph import StateGraph, START, END
from .models import AgentState
from .nodes import process_input_node, review_decision_node, llm_response_node, human_review_node, sentiment_analysis_node, intent_recognition_node, knowledge_retrieval_node
from .conditions import should_use_human_review


def build_chat_workflow():
    """
    构建聊天工作流
    
    Returns:
        编译后的工作流应用
    """
    # 创建工作流图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("process_input", process_input_node)
    workflow.add_node("sentiment_analysis", sentiment_analysis_node)
    workflow.add_node("intent_recognition", intent_recognition_node)  # 新增意图识别节点
    workflow.add_node("knowledge_retrieval", knowledge_retrieval_node)  # 新增知识库检索节点
    workflow.add_node("review_decision", review_decision_node)
    workflow.add_node("llm_response", llm_response_node)
    workflow.add_node("human_review", human_review_node)
    
    # 设置边
    workflow.add_edge(START, "process_input")
    workflow.add_edge("process_input", "sentiment_analysis")
    workflow.add_edge("sentiment_analysis", "intent_recognition")  # 情感分析后进行意图识别
    workflow.add_edge("intent_recognition", "knowledge_retrieval")  # 意图识别后进行知识库检索
    workflow.add_edge("knowledge_retrieval", "review_decision")  # 知识库检索后进行审核决策
    
    # 条件路由
    workflow.add_conditional_edges(
        "review_decision",
        should_use_human_review,
        {
            "human_review": "human_review",
            "llm_response": "llm_response"
        }
    )
    
    # 完成流程
    workflow.add_edge("llm_response", END)
    workflow.add_edge("human_review", END)
    
    # 编译
    app = workflow.compile()
    
    return app
