# AIchat4.11 多智能体 MCP 架构改造指南

## 📋 目录

1. [改造目标](#改造目标)
2. [架构设计](#架构设计)
3. [实施步骤](#实施步骤)
4. [核心代码](#核心代码)
5. [迁移策略](#迁移策略)
6. [测试方案](#测试方案)

---

## 🎯 改造目标

### 当前架构痛点
- ❌ 单体 LangGraph 工作流,耦合度高
- ❌ 新增功能需修改核心 workflow
- ❌ 难以独立测试各个模块
- ❌ 扩展性受限

### 目标架构优势
- ✅ **高内聚**: 每个智能体职责单一
- ✅ **低耦合**: 通过 MCP 消息总线通信
- ✅ **可扩展**: 新增智能体无需修改现有代码
- ✅ **可测试**: 每个智能体可独立测试
- ✅ **可替换**: 轻松替换某个智能体的实现

---

## 🏗️ 架构设计

### 整体架构图

```
┌──────────────────────────────────────────────────────┐
│                  FastAPI Layer                        │
│            (api_server.py - HTTP接口)                 │
└────────────────────┬─────────────────────────────────┘
                     │ WebSocket/HTTP
┌────────────────────▼─────────────────────────────────┐
│              Message Bus (MCP)                        │
│         (异步消息队列 + 路由分发)                      │
└──┬────────┬────────┬────────┬────────┬───────────────┘
   │        │        │        │        │
┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼────────┐
│Coord│ │RAG  │ │Sent │ │Int  │ │LLM        │
│     │ │Agent│ │Agent│ │Agent│ │Response   │
│协调者│ │检索 │ │情感 │ │意图 │ │响应       │
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └────┬──────┘
   │        │        │        │         │
   └────────┴────────┴────────┴─────────┘
              复用现有 LLM 模块
         (RAG, emotion, intent, Memory)
```

### 智能体角色定义

| 智能体 | 职责 | 输入 | 输出 |
|--------|------|------|------|
| **Coordinator** | 协调者,主控流程 | 用户消息 | 最终回复 |
| **RAG Agent** | 知识库检索 | 用户问题 | 检索结果 |
| **Sentiment Agent** | 情感分析 | 文本 | 情感标签+分数 |
| **Intent Agent** | 意图识别 | 文本 | 意图类型+置信度 |
| **Memory Agent** | 记忆管理 | 对话历史 | 总结/检索 |
| **LLM Response Agent** | 生成回复 | 上下文信息 | AI 回复 |

---

## 🔧 实施步骤

### 阶段 1: 基础设施搭建 (1-2天)

#### Step 1.1: 创建 MCP 协议层

已创建文件:
- ✅ `backendtest/mcp/protocol.py` - 消息协议定义

需要创建:
- ⏳ `backendtest/mcp/message_bus.py` - 消息总线
- ⏳ `backendtest/mcp/agent_base.py` - 智能体基类
- ⏳ `backendtest/mcp/__init__.py` - 模块导出

#### Step 1.2: 安装依赖

```bash
pip install asyncio aiohttp redis  # Redis 用于消息队列(可选)
```

### 阶段 2: 智能体开发 (3-5天)

#### Step 2.1: 创建智能体基类

```python
# backendtest/mcp/agent_base.py
from abc import ABC, abstractmethod
from typing import Any, Dict
from .protocol import MCPMessage, MCPResponse


class BaseAgent(ABC):
    """
    智能体基类
    
    所有智能体必须继承此类并实现 handle_message 方法
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.message_handlers = {}
        
        print(f"🤖 智能体初始化: {agent_name}")
    
    @abstractmethod
    async def handle_message(self, message: MCPMessage) -> MCPResponse:
        """
        处理接收到的消息
        
        Args:
            message: MCP 消息对象
            
        Returns:
            MCP 响应对象
        """
        pass
    
    def register_handler(self, action: str, handler):
        """注册动作处理器"""
        self.message_handlers[action] = handler
        print(f"  📝 注册处理器: {action}")
    
    async def process(self, message: MCPMessage) -> MCPResponse:
        """
        处理消息的分发逻辑
        
        根据 message.action 调用对应的处理器
        """
        action = message.action
        
        if action in self.message_handlers:
            handler = self.message_handlers[action]
            try:
                result = await handler(message.payload)
                return MCPResponse(
                    success=True,
                    data=result,
                    message_id=message.message_id
                )
            except Exception as e:
                return MCPResponse(
                    success=False,
                    error=str(e),
                    message_id=message.message_id
                )
        else:
            return MCPResponse(
                success=False,
                error=f"未注册的动作处理器: {action}",
                message_id=message.message_id
            )
```

#### Step 2.2: 实现各个智能体

**示例: RAG Agent**

```python
# backendtest/agents/rag_agent.py
from ..mcp.agent_base import BaseAgent
from ..mcp.protocol import MCPMessage, MCPResponse
from ..LLM.RAG import knowledge_base_manager


class RAGAgent(BaseAgent):
    """RAG 检索智能体"""
    
    def __init__(self):
        super().__init__("RAG_Agent")
        
        # 注册处理器
        self.register_handler("retrieve_knowledge", self.handle_retrieve)
        self.register_handler("get_summary", self.handle_get_summary)
    
    async def handle_retrieve(self, payload: dict) -> dict:
        """处理知识检索请求"""
        user_input = payload.get("user_input", "")
        
        # 使用现有的 RAG 模块
        from ..LLM.nodes import knowledge_retrieval_node
        
        # 构造状态
        state = {
            "user_input": user_input,
            "messages": [],
            "ai_response": "",
            "needs_human_review": False,
            "sentiment_result": {},
            "intent_result": {},
            "keywords_result": {},
            "entities_result": {},
            "rag_retrieved_content": "",
            "rag_used": False
        }
        
        result = await knowledge_retrieval_node(state)
        
        return {
            "content": result.get("rag_retrieved_content", ""),
            "used": result.get("rag_used", False)
        }
    
    async def handle_get_summary(self, payload: dict) -> dict:
        """获取知识库摘要"""
        summary = await knowledge_base_manager.get_file_summary()
        return {"summary": summary}
    
    async def handle_message(self, message: MCPMessage) -> MCPResponse:
        return await self.process(message)
```

**示例: Sentiment Agent**

```python
# backendtest/agents/sentiment_agent.py
from ..mcp.agent_base import BaseAgent
from ..mcp.protocol import MCPMessage, MCPResponse


class SentimentAgent(BaseAgent):
    """情感分析智能体"""
    
    def __init__(self):
        super().__init__("Sentiment_Agent")
        self.register_handler("analyze_sentiment", self.handle_analyze)
    
    async def handle_analyze(self, payload: dict) -> dict:
        """处理情感分析请求"""
        text = payload.get("text", "")
        
        # 使用现有的情感分析模块
        from ..LLM.emotion.sentiment_analyzer import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze(text)
        
        return result
    
    async def handle_message(self, message: MCPMessage) -> MCPResponse:
        return await self.process(message)
```

其他智能体类似实现...

### 阶段 3: 消息总线实现 (2-3天)

```python
# backendtest/mcp/message_bus.py
import asyncio
from typing import Dict, Callable, List
from .protocol import MCPMessage, MCPResponse, AgentRole


class MessageBus:
    """
    消息总线
    
    负责:
    - 消息路由
    - 智能体注册
    - 异步消息处理
    """
    
    def __init__(self):
        self.agents: Dict[AgentRole, any] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.subscribers: Dict[str, List[Callable]] = {}
        
        print("🚌 消息总线初始化完成")
    
    def register_agent(self, role: AgentRole, agent):
        """注册智能体"""
        self.agents[role] = agent
        print(f"✅ 注册智能体: {role.value}")
    
    async def send_message(self, message: MCPMessage) -> MCPResponse:
        """
        发送消息到指定智能体
        
        Args:
            message: MCP 消息对象
            
        Returns:
            MCP 响应对象
        """
        receiver = message.receiver
        
        if receiver not in self.agents:
            return MCPResponse(
                success=False,
                error=f"未找到接收者: {receiver}",
                message_id=message.message_id
            )
        
        agent = self.agents[receiver]
        response = await agent.handle_message(message)
        
        return response
    
    async def broadcast(self, message: MCPMessage) -> List[MCPResponse]:
        """广播消息给所有智能体"""
        responses = []
        
        for role, agent in self.agents.items():
            if role != message.sender:  # 不发送给发送者自己
                response = await agent.handle_message(message)
                responses.append(response)
        
        return responses
    
    async def start(self):
        """启动消息总线(持续监听队列)"""
        print("🚀 消息总线启动,开始监听...")
        
        while True:
            message = await self.message_queue.get()
            
            try:
                response = await self.send_message(message)
                
                # 通知订阅者
                if message.conversation_id in self.subscribers:
                    for callback in self.subscribers[message.conversation_id]:
                        await callback(response)
            
            except Exception as e:
                print(f"❌ 处理消息失败: {e}")
            
            finally:
                self.message_queue.task_done()
```

### 阶段 4: 协调者智能体 (核心,2-3天)

```python
# backendtest/agents/coordinator.py
from ..mcp.agent_base import BaseAgent
from ..mcp.protocol import (
    MCPMessage, MCPResponse, AgentRole,
    create_rag_request, create_sentiment_request,
    create_intent_request, create_llm_response_request
)


class CoordinatorAgent(BaseAgent):
    """
    协调者智能体
    
    职责:
    1. 接收用户消息
    2. 并行调用各个专业智能体
    3. 整合结果
    4. 调用 LLM 生成最终回复
    """
    
    def __init__(self, message_bus):
        super().__init__("Coordinator")
        self.message_bus = message_bus
        self.register_handler("process_user_message", self.handle_user_message)
    
    async def handle_user_message(self, payload: dict) -> dict:
        """处理用户消息的主流程"""
        user_input = payload.get("user_input", "")
        conversation_id = payload.get("conversation_id")
        
        print(f"\n📨 收到用户消息: {user_input[:50]}...")
        
        # 步骤1: 并行调用情感分析和意图识别
        sentiment_task = self.message_bus.send_message(
            create_sentiment_request(user_input, conversation_id)
        )
        
        intent_task = self.message_bus.send_message(
            create_intent_request(user_input, conversation_id)
        )
        
        # 步骤2: 判断是否需要 RAG 检索
        rag_needed = self._should_use_rag(user_input)
        rag_result = None
        
        if rag_needed:
            print("📚 触发 RAG 检索...")
            rag_task = self.message_bus.send_message(
                create_rag_request(user_input, conversation_id)
            )
            rag_response = await rag_task
            rag_result = rag_response.data
        
        # 等待情感和意图分析完成
        sentiment_response = await sentiment_task
        intent_response = await intent_task
        
        # 步骤3: 整合上下文
        context = {
            "user_input": user_input,
            "sentiment": sentiment_response.data if sentiment_response.success else {},
            "intent": intent_response.data if intent_response.success else {},
            "rag_content": rag_result.get("content", "") if rag_result else "",
            "rag_used": rag_result.get("used", False) if rag_result else False
        }
        
        # 步骤4: 调用 LLM 生成回复
        llm_response = await self.message_bus.send_message(
            create_llm_response_request(user_input, context, conversation_id)
        )
        
        final_response = llm_response.data if llm_response.success else "抱歉,发生错误"
        
        print(f"✅ 生成回复: {final_response[:100]}...")
        
        return {
            "response": final_response,
            "context": context
        }
    
    def _should_use_rag(self, user_input: str) -> bool:
        """判断是否需要使用 RAG"""
        keywords = ["产品", "规格", "参数", "技术", "如何", "怎么"]
        return any(kw in user_input for kw in keywords)
    
    async def handle_message(self, message: MCPMessage) -> MCPResponse:
        return await self.process(message)
```

### 阶段 5: API 层改造 (1天)

修改 `api_server.py`:

```python
# 在 api_server.py 中
from backendtest.mcp.message_bus import MessageBus
from backendtest.mcp.protocol import AgentRole
from backendtest.agents.coordinator import CoordinatorAgent
from backendtest.agents.rag_agent import RAGAgent
from backendtest.agents.sentiment_agent import SentimentAgent
# ... 导入其他智能体


# 全局变量
message_bus = None
coordinator = None


def initialize_multi_agent_system():
    """初始化多智能体系统"""
    global message_bus, coordinator
    
    # 创建消息总线
    message_bus = MessageBus()
    
    # 注册智能体
    message_bus.register_agent(AgentRole.RAG_AGENT, RAGAgent())
    message_bus.register_agent(AgentRole.SENTIMENT_AGENT, SentimentAgent())
    # ... 注册其他智能体
    
    # 创建协调者
    coordinator = CoordinatorAgent(message_bus)
    message_bus.register_agent(AgentRole.COORDINATOR, coordinator)
    
    print("✅ 多智能体系统初始化完成")


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    initialize_multi_agent_system()
    
    # 启动消息总线(后台任务)
    asyncio.create_task(message_bus.start())


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """聊天接口 - 使用多智能体系统"""
    try:
        last_message = request.messages[-1]
        
        # 通过协调者处理
        response = await message_bus.send_message(
            MCPMessage(
                sender=AgentRole.COORDINATOR,
                receiver=AgentRole.COORDINATOR,
                action="process_user_message",
                payload={
                    "user_input": last_message.content,
                    "conversation_id": request.conversation_id
                }
            )
        )
        
        return ChatResponse(
            message=response.data["response"] if response.success else "处理失败"
        )
    
    except Exception as e:
        return ChatResponse(message="", error=str(e))
```

---

## 🔄 迁移策略

### 渐进式迁移(推荐)

```
第1周: 基础设施
  ├─ 创建 MCP 协议层
  ├─ 实现消息总线
  └─ 编写智能体基类

第2周: 核心智能体
  ├─ 实现 Coordinator
  ├─ 实现 RAG Agent
  └─ 实现 Sentiment/Intent Agent

第3周: 集成测试
  ├─ 单元测试各个智能体
  ├─ 集成测试消息流转
  └─ 性能测试和优化

第4周: 灰度发布
  ├─ 保留旧 LangGraph 工作流
  ├─ 新请求走多智能体架构
  └─ 对比效果,逐步切换
```

### 回滚方案

```python
# api_server.py 中添加开关
USE_MULTI_AGENT = os.getenv("USE_MULTI_AGENT", "false").lower() == "true"

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if USE_MULTI_AGENT:
        # 使用多智能体架构
        return await multi_agent_chat(request)
    else:
        # 使用原有 LangGraph 工作流
        return await langgraph_chat(request)
```

---

## 🧪 测试方案

### 单元测试

```python
# tests/test_agents.py
import pytest
from backendtest.agents.rag_agent import RAGAgent
from backendtest.mcp.protocol import create_rag_request


@pytest.mark.asyncio
async def test_rag_agent():
    """测试 RAG 智能体"""
    agent = RAGAgent()
    
    message = create_rag_request("SW-2100的电池续航?")
    response = await agent.handle_message(message)
    
    assert response.success is True
    assert "content" in response.data
```

### 集成测试

```python
# tests/test_multi_agent_flow.py
@pytest.mark.asyncio
async def test_full_conversation():
    """测试完整对话流程"""
    # 初始化系统
    initialize_multi_agent_system()
    
    # 发送用户消息
    response = await message_bus.send_message(...)
    
    # 验证结果
    assert response.success
    assert len(response.data["response"]) > 0
```

---

## 📊 预期收益

### 性能对比

| 指标 | LangGraph | 多智能体 | 提升 |
|------|-----------|----------|------|
| 模块独立性 | ⭐⭐ | ⭐⭐⭐⭐⭐ | +150% |
| 可测试性 | ⭐⭐ | ⭐⭐⭐⭐⭐ | +150% |
| 扩展性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | +67% |
| 维护成本 | 高 | 低 | -40% |

### 开发效率

- ✅ 新增功能: 只需添加新智能体,无需修改现有代码
- ✅ 调试难度: 每个智能体可独立调试
- ✅ 团队协作: 不同开发者可并行开发不同智能体

---

## 🎓 学习资源

1. **MCP 协议规范**: https://modelcontextprotocol.io/
2. **智能体设计模式**: 《Building Multi-Agent Systems》
3. **消息队列最佳实践**: RabbitMQ/Redis 官方文档
4. **你的历史经验**: 参考旅行地图项目的多智能体重构

---

## 💡 下一步行动

### 立即开始

1. ✅ 阅读本指南,理解整体架构
2. ⏳ 运行 `python backendtest/mcp/protocol.py` 查看消息示例
3. ⏳ 创建 `backendtest/mcp/__init__.py` 和 `message_bus.py`
4. ⏳ 实现第一个智能体(RAG Agent)

### 遇到问题?

- 查看 `RAG集成说明.md` 了解现有 RAG 模块
- 参考旅行地图项目的多智能体实现
- 每个智能体都复用现有 LLM 模块,无需重写

---

**祝你重构顺利! 🚀**

有任何问题随时问我!
