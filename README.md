# AIchattest 项目说明

## 📁 项目结构

```
AIchattest/
├── backendtest/          # 后端代码（FastAPI + LangGraph）
│   ├── LLM/             # LLM 引擎和工具
│   │   ├── Memory/      # 记忆管理模块
│   │   │   ├── ContextAtlas-main/  # ContextAtlas 知识库
│   │   │   ├── knowledge_base.py   # 知识库封装层
│   │   │   └── memory_manager.py   # 对话记忆管理器
│   │   ├── nodes.py     # LangGraph 节点定义
│   │   ├── tools.py     # 工具函数集合
│   │   └── ...
│   ├── api_server.py    # FastAPI 服务器
│   └── config.py        # 配置文件
├── frontendtest/         # 前端代码（React + Vite）
│   └── src/
├── tests/                # 测试文件
│   ├── test_kb_simple.py                    # 知识库简单测试
│   ├── test_e2e_kb_integration.py           # 端到端集成测试
│   ├── test_contextatlas_integration.py     # ContextAtlas 集成测试
│   ├── test_llm_emotion.py                  # LLM 情感分析测试
│   ├── test_new_features.py                 # 新功能测试
│   └── test_sentiment_integration.py        # 情感分析集成测试
├── docs/                   # 文档
│   ├── ContextAtlas集成说明.md              # ContextAtlas 使用指南
│   ├── 情感分析功能使用说明.md               # 情感分析功能说明
│   ├── 连接配置说明.md                      # API 配置说明
│   ├── 运行说明.txt                         # 运行指南
│   ├── 如何运行？.txt                       # 快速开始
│   └── 启动说明.bat                         # Windows 启动脚本
└── __init__.py
```

## 🚀 快速开始

### 1. 启动后端
```bash
cd backendtest
python api_server.py
```

### 2. 启动前端
```bash
cd frontendtest
npm run dev
```

### 3. 或使用启动脚本
```bash
docs\启动说明.bat
```

## 🧪 运行测试

```bash
# 运行所有测试
cd tests
python -m pytest

# 运行特定测试
python test_kb_simple.py
python test_e2e_kb_integration.py
```

## 📚 主要功能

### 1. 智能对话系统
- 基于 LangGraph 的工作流引擎
- 支持多轮对话和上下文记忆
- 集成多种工具（天气、计算、搜索等）

### 2. ContextAtlas 知识库
- 语义代码检索
- 结构化记忆管理
- 自动知识沉淀

### 3. 情感分析
- 多维度情感识别
- 意图分析
- 关键词提取

## ⚙️ 配置说明

编辑 `backendtest/config.py` 配置 API Keys：
- 通义千问 API
- Tavily 搜索 API
- 其他服务配置

详见 `docs/连接配置说明.md`

## 📖 文档

- [ContextAtlas 集成说明](docs/ContextAtlas集成说明.md)
- [情感分析功能说明](docs/情感分析功能使用说明.md)
- [连接配置说明](docs/连接配置说明.md)
- [运行说明](docs/运行说明.txt)

## 🔧 技术栈

**后端：**
- FastAPI
- LangGraph
- LangChain
- Python 3.10+

**前端：**
- React
- TypeScript
- Vite
- TailwindCSS

**AI/ML：**
- 通义千问 (Qwen)
- ContextAtlas
- 情感分析模型

## 📝 更新日志

### 2026-04-09
- ✅ 集成 ContextAtlas 知识库
- ✅ 添加智能代码检索功能
- ✅ 优化项目结构，分离测试和文档

### 更早版本
- 实现基础对话功能
- 添加工具调用支持
- 集成情感分析模块

---

**最后更新**: 2026-04-09
