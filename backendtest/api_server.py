"""
API 接口层 - FastAPI 实现
负责处理 HTTP 请求、与前端通信
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio

# 导入 LangGraph 引擎
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from LLM.langgraph_engine import create_langgraph_service

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

# ==================== 数据模型 ====================

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


# ==================== API 路由 ====================

@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "message": "AI Chat API with LangGraph is running"}


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
    真正的流式输出（从 LLM 实时获取）
    """
    from fastapi.responses import StreamingResponse
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
            
            # 使用真正的流式方法
            async for chunk in service.chat_stream(last_message.content):
                # 发送文本片段
                chunk_data = {"content": chunk}
                yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
            
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


@app.get("/api/greeting")
async def get_greeting():
    """
    获取 AI 问候语
    读取 permanent_summary.json 文件，使用 LLM 生成个性化时段问候但不写入记忆
    """
    try:
        import json
        from pathlib import Path
        from datetime import datetime
        
        # 获取当前模块所在目录
        current_dir = Path(__file__).parent
        summary_file = current_dir / "LLM" / "Memory" / "Date" / "permanent_summary.json"
        
        if not summary_file.exists():
            # 文件不存在时也使用时段问候
            from datetime import datetime
            current_hour = datetime.now().hour
            if 5 <= current_hour < 12:
                time_period = "早上"
            elif 12 <= current_hour < 14:
                time_period = "中午"
            elif 14 <= current_hour < 18:
                time_period = "下午"
            else:
                time_period = "晚上"
            
            # 使用 LLM 生成首次见面的问候
            try:
                from langchain_openai import ChatOpenAI
                try:
                    from .config import qwen_base_url, qwen_api_key
                except ImportError:
                    from config import qwen_base_url, qwen_api_key
                
                llm = ChatOpenAI(
                    model="qwen-plus",
                    base_url=qwen_base_url,
                    api_key=qwen_api_key,
                    temperature=0.7,
                )
                
                prompt = f"""你是一个亲切友好的 AI 助手。现在是{time_period}。

这是用户第一次访问，还没有任何历史对话记录。

请生成一句简洁自然的{time_period}问候语（不超过 30 字），要求：
1. 以"{time_period}好"开头
2. 表达欢迎之意
3. 邀请用户开始对话
4. 语气轻松自然，不要死板

直接回复问候语即可，不要其他内容。"""
                
                from langchain_core.messages import HumanMessage
                response = await llm.ainvoke([HumanMessage(content=prompt)])
                greeting = response.content.strip()
                
                return {
                    "greeting": greeting,
                    "has_summary": False,
                    "time_period": time_period
                }
            except Exception as e:
                # 如果生成失败，返回简单问候
                return {
                    "greeting": f"{time_period}好！我是你的 AI 助手，很高兴见到你。",
                    "has_summary": False,
                    "error": str(e)
                }
        
        # 读取 permanent_summary.json
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)
        
        # 根据当前时间判断时段
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            time_period = "早上"
        elif 12 <= current_hour < 14:
            time_period = "中午"
        elif 14 <= current_hour < 18:
            time_period = "下午"
        else:
            time_period = "晚上"
        
        # 提取关键信息
        summary = summary_data.get('summary', '')
        last_updated = summary_data.get('last_updated', '')
        
        # 使用 LLM 生成个性化问候
        from langchain_openai import ChatOpenAI
        
        # 尝试不同的导入方式
        try:
            from .config import qwen_base_url, qwen_api_key
        except ImportError:
            from config import qwen_base_url, qwen_api_key
        
        llm = ChatOpenAI(
            model="qwen-plus",
            base_url=qwen_base_url,
            api_key=qwen_api_key,
            temperature=0.7,
        )
        
        # 构建提示词
        prompt = f"""你是一个亲切友好的 AI 助手。现在是{time_period}。

用户之前的对话总结是：
{summary if summary else '首次见面'}

最后更新时间：{last_updated if last_updated else '未知'}

请生成一句简洁自然的{time_period}问候语（不超过 50 字），要求：
1. 以"{time_period}好"开头
2. 简要提及之前讨论的内容（如果有）
3. 询问进展并邀请继续
4. 语气轻松自然，不要死板

直接回复问候语即可，不要其他内容。"""
        
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        greeting = response.content.strip()
        
        return {
            "greeting": greeting,
            "has_summary": True,
            "time_period": time_period,
            "last_updated": last_updated
        }
    except Exception as e:
        # 如果生成失败，返回默认问候语
        time_fallback = "你好"
        try:
            current_hour = datetime.now().hour
            if 5 <= current_hour < 12:
                time_fallback = "早上好"
            elif 12 <= current_hour < 14:
                time_fallback = "中午好"
            elif 14 <= current_hour < 18:
                time_fallback = "下午好"
            else:
                time_fallback = "晚上好"
        except:
            pass
        
        return {
            "greeting": f"{time_fallback}好！我是你的 AI 助手，很高兴见到你。",
            "has_summary": False,
            "error": str(e)
        }


@app.delete("/api/chat/history")
async def clear_history():
    """清空对话历史"""
    try:
        service = get_chat_service()
        service.clear_history()
        return {"status": "ok", "message": "对话历史已清空"}
    except Exception as e:
        return {"error": str(e)}


# ==================== 应用入口 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
