"""
AI Chat Backend with LangGraph - FastAPI 实现
提供聊天 API 接口支持（基于 LangGraph 智能对话引擎）
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json

# 导入 LangGraph 引擎
from .langgraph_engine import create_langgraph_service

app = FastAPI(title="AI Chat API with LangGraph", version="2.0.0")

# CORS 配置 - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*",  # 开发环境允许所有来源
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求模型
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    message: str
    error: Optional[str] = None


# ==================== 服务实例 ====================

# 全局聊天服务实例
chat_service = None


def get_chat_service():
    """获取或创建聊天服务实例"""
    global chat_service
    if chat_service is None:
        chat_service = create_langgraph_service()
    return chat_service


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "message": "AI Chat API is running"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    普通聊天接口
    使用 LangGraph 工作流处理用户消息
    
    Args:
        request: 包含消息列表的请求体
        
    Returns:
        AI 回复
    """
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="消息列表不能为空")
        
        # 获取最后一条用户消息
        last_message = request.messages[-1]
        if last_message.role != "user":
            raise HTTPException(status_code=400, detail="最后一条消息必须是用户消息")
        
        # 获取聊天服务
        service = get_chat_service()
        
        # 调用 LangGraph 引擎
        ai_response = await service.chat(last_message.content)
        
        return ChatResponse(message=ai_response)
    
    except HTTPException:
        raise
    except Exception as e:
        return ChatResponse(message="", error=str(e))


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口
    使用 Server-Sent Events (SSE) 返回 AI 回复
    
    注意：LangGraph 本身不支持流式输出
    这里使用模拟流式效果（逐字发送）
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    import json
    
    async def generate_stream():
        try:
            if not request.messages:
                raise HTTPException(status_code=400, detail="消息列表不能为空")
            
            # 获取最后一条用户消息
            last_message = request.messages[-1]
            if last_message.role != "user":
                raise HTTPException(status_code=400, detail="最后一条消息必须是用户消息")
            
            # 获取聊天服务
            service = get_chat_service()
            
            # 获取完整回复
            full_response = await service.chat(last_message.content)
            
            # 模拟流式输出（逐字发送）
            for char in full_response:
                chunk_data = {"content": char}
                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.03)  # 控制输出速度
            
            # 结束标记
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            # 发送错误信息
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/chat/history")
async def get_history():
    """获取对话历史"""
    try:
        service = get_chat_service()
        history = service.get_history()
        
        return {
            "messages": [
                {"role": msg.type, "content": msg.content}
                for msg in history
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/chat/history")
async def clear_history():
    """清空对话历史"""
    try:
        service = get_chat_service()
        service.clear_history()
        return {"status": "ok", "message": "对话历史已清空"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
