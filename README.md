# Intelligent-Customer-Service-Assistant - 基于 LangGraph 工作流的 AI 智能客服系统

## 📖 项目简介

Intelligent-Customer-Service-Assistant 是一个采用**LangGraph 状态机工作流架构**的智能客服平台，通过多节点协作 Pipeline 实现端到端的对话理解、情感分析、意图识别与知识库检索增强生成（RAG）。系统创新性地将 ContextAtlas 语义检索引擎与多维度情感分析模块深度融合，构建了包含输入处理、情感计算、知识检索、LLM 响应生成的完整 AI 对话链路，解决了传统客服系统在上下文理解、个性化服务和知识准确性上的痛点。

本项目不仅实现了自然语言驱动的交互式智能问答，更通过**模块化节点设计**和**条件路由机制**，为复杂对话场景提供了可扩展的工程化解决方案。

---

## 🎯 核心功能

### 1. 多模态意图解析引擎
- **混合意图识别**：基于 LLM + 规则引擎，精准区分咨询、闲聊、投诉、技术支持等意图类型
- **置信度评估**：输出意图分类结果及置信度分数，支持低置信度时的人工接管
- **上下文感知路由**：结合对话历史动态调整意图判断策略

### 2. RAG 知识增强检索 Pipeline
```
用户提问 → 关键词提取 → 知识库摘要匹配 → 文件级检索 → 内容注入 → LLM 生成
```
- **智能分块策略**：大文件自动分割并生成块级摘要，提升检索精度
- **并发检索优化**：多文件并行读取，减少 I/O 等待时间
- **断点续传机制**：缓存已生成的摘要，避免重复计算
- **知识地图构建**：自动生成知识库全局摘要，辅助 LLM 理解知识结构

### 3. 多维度情感分析系统
- **词典规则引擎**：集成 cntext 中文情感词典，支持细粒度情感计算
- **多字典融合**：结合正面/负面/程度副词/否定词等多维度词典
- **实时情感追踪**：每轮对话实时更新情感状态，支持情绪波动检测
- **降级容错机制**：LLM 异常时自动切换至规则匹配，保证服务可用性

### 4. 持久化记忆管理系统
- **双层存储架构**：内存缓存（快速访问）+ JSON 文件持久化（断电恢复）
- **时段感知问候**：根据当前时间（早/中/晚）生成个性化问候语
- **对话历史压缩**：定期总结长对话，提取关键信息存入永久记忆
- **会话状态恢复**：支持中断后从上次对话继续，保持上下文连贯性

### 5. 流式响应交互界面
- **SSE 实时推送**：Server-Sent Events 实现真正的流式输出
- **打字机效果**：逐字渲染 AI 回复，模拟自然对话节奏
- **响应式设计**：适配桌面端与移动端，流畅的交互动画

---

## 💡 技术亮点

### 🏗️ 架构设计创新

#### 1. LangGraph 状态机工作流
- **节点化设计**：将对话流程拆解为独立节点（Input → Sentiment → Intent → RAG → LLM → Review）
- **条件路由**：基于节点输出动态决定下一步执行路径（如：低置信度触发人工审核）
- **状态传递**：AgentState 在各节点间共享，避免数据冗余
- **可视化调试**：LangGraph Studio 支持工作流可视化与断点调试

#### 2. ContextAtlas 语义检索引擎
- **代码级语义理解**：超越关键词匹配，实现基于语义相似度的智能检索
- **结构化记忆管理**：自动沉淀对话中的关键知识点，形成可复用的知识图谱
- **增量更新机制**：新知识自动融入现有索引，无需重建整个向量库

#### 3. 自定义 MCP 协议（规划中）
```python
{
    "message_id": "uuid",           # 消息追踪
    "message_type": "request",      # request/response/notification/error
    "sender": "coordinator",        # 发送者标识
    "receiver": "rag_agent",        # 目标智能体
    "action": "retrieve_knowledge", # 动作指令
    "payload": {...},               # 业务数据
    "priority": "high",             # 优先级控制
    "timestamp": "ISO8601"          # 时序保证
}
```
- **标准化消息格式**：统一的请求/响应契约，降低集成复杂度
- **异步消息传递**：基于 asyncio 的非阻塞通信，提升并发性能
- **智能体解耦**：为未来多智能体架构预留扩展空间

### 🤖 算法与模型优化

#### 1. 混合情感分析策略
- **第一层**：cntext 词典规则快速匹配（毫秒级响应）
- **第二层**：LLM 语义情感分析（复杂语境理解）
- **融合策略**：加权平均两种结果，平衡速度与准确性

#### 2. 智能 RAG 触发机制
- **关键词检测**：检测到"产品"、"规格"、"参数"等关键词时触发检索
- **意图判断**：咨询类意图自动启用 RAG，闲聊类跳过检索
- **缓存优化**：高频问题答案缓存，减少重复检索开销

#### 3. 流式输出生成
- **真实流式**：直接从 LLM API 获取 token 流，非前端模拟
- **背压控制**：根据客户端消费速度动态调整推送频率
- **错误隔离**：流式传输异常时优雅降级为普通响应

---

## 🛠️ 技术栈

### 后端技术
- **Web 框架**：FastAPI 0.109+（异步高性能 API）
- **工作流引擎**：LangGraph 0.1.x（状态机驱动对话流程）
- **AI 模型**：通义千问 qwen-plus（阿里云 DashScope）
- **检索引擎**：ContextAtlas（语义代码检索）
- **情感分析**：cntext 中文情感词典库
- **数据验证**：Pydantic v2（类型安全的数据模型）
- **异步运行时**：asyncio + uvicorn（ASGI 服务器）
- **搜索 API**：Tavily Search（网络信息检索）

### 前端技术
- **核心框架**：React 18.3 + TypeScript 5.x
- **构建工具**：Vite 6.3（极速开发体验）
- **UI 组件库**：
  - Material-UI (MUI) 7.3（企业级组件）
  - shadcn/ui（基于 Radix UI 的可定制组件）
  - Lucide React（现代化图标库）
- **样式方案**：Tailwind CSS 4.x（原子化 CSS）
- **状态管理**：React Hooks + Context API
- **动画库**：Framer Motion（流畅交互动画）
- **富文本**：react-slick（轮播组件）

### 开发工具
- **包管理**：npm / pnpm
- **代码规范**：ESLint + Prettier（前端）
- **版本控制**：Git
- **API 测试**：FastAPI 内置 Swagger UI (`/docs`)
- **测试框架**：pytest + pytest-asyncio

---

## ⚙️ 环境依赖与配置

### 系统要求
- **Python**：3.10+
- **Node.js**：16+
- **操作系统**：Windows / macOS / Linux

### 后端环境配置

#### 1. 安装依赖
```bash
cd backendtest
pip install -r requirements.txt
```

主要依赖包括：
```txt
fastapi
uvicorn
langgraph
langchain
langchain-openai
aiofiles
tiktoken
cntext
contextatlas
```

#### 2. 配置环境变量
编辑 `backendtest/config.py` 文件：
```python
# 通义千问 API（必需）
qwen_base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
qwen_api_key = "sk-your-api-key-here"

# Tavily 搜索 API（可选）
tavily_api_key = "tvly-your-api-key"
```

**获取 API Key：**
- 通义千问：[阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/)
- Tavily Search：[Tavily 官网](https://tavily.com/)

### 前端环境配置

#### 1. 安装依赖
```bash
cd frontendtest
npm install
# 或使用 pnpm
pnpm install
```

#### 2. 配置后端地址（可选）
默认连接 `http://localhost:8000`，如需修改请编辑前端代码中的 API 基础 URL。

---

## 🚀 前端部署与运行

### 开发模式
```bash
cd frontendtest
npm run dev
```
访问：`http://localhost:5173`

### 生产构建
```bash
npm run build
# 生成的静态文件在 dist/ 目录
```

### 预览生产构建
```bash
npm run preview
```
---
## 🚀 后端部署与运行

### 方式一：手动启动
```bash
cd backendtest
python api_server.py
```

### 方式二：使用 Uvicorn 命令行
```bash
cd backendtest
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 验证服务
- **健康检查**：`http://localhost:8000/`
- **API 文档**：`http://localhost:8000/docs`（Swagger UI）

---

## 🔮 未来演进方向

### 短期优化（1-3 个月）
- [ ] 完成多智能体 MCP 架构改造（参考《多智能体MCP架构改造指南.md》）
- [ ] 引入 Redis 缓存层，优化高频查询性能
- [ ] 实现智能体重试机制与熔断器模式
- [ ] 添加 Prometheus + Grafana 监控告警

### 中期扩展（3-6 个月）
- [ ] 引入分布式消息队列（RabbitMQ/Kafka）
- [ ] 支持智能体动态发现与负载均衡
- [ ] 添加专业智能体（订单查询、售后工单、预算规划）
- [ ] 实现多用户会话隔离与权限管理

### 长期愿景（6-12 个月）
- [ ] 容器化部署（Docker + Kubernetes）
- [ ] 微服务拆分（独立部署各智能体）
- [ ] 支持插件市场（第三方智能体接入）
- [ ] 多语言国际化支持

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

---

**用 AI 重新定义客户服务体验** 💬🤖✨
