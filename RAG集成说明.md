# RAG 功能集成说明

## 📋 概述

已成功将 RAG (Retrieval-Augmented Generation) 功能集成到 AIchat4.11 项目中。RAG 允许 AI 助手从结构化知识库中检索相关信息,提供更准确、基于事实的回答。

## 🎯 核心功能

### 1. 知识库管理 (`LLM/RAG/knowledge_base.py`)
- **文件检索**: 支持检索单个文件、整个目录或所有文件
- **知识地图**: 自动生成知识库摘要,帮助 LLM 理解知识结构
- **异步读取**: 使用 aiofiles 实现高效的异步文件操作

### 2. LLM Provider 抽象层 (`LLM/RAG/llm_provider.py`)
- **统一接口**: 兼容 OpenAI、Gemini、Claude 及任何 OpenAI 格式 API
- **流式响应**: 支持真正的流式输出
- **错误处理**: 完善的异常处理和重试机制

### 3. 知识库摘要生成器 (`LLM/RAG/generate_summary.py`)
- **智能分块**: 大文件自动分割并生成块级摘要
- **并发处理**: 多文件并行生成,提高效率
- **断点续传**: 缓存机制支持中断后继续

### 4. LangGraph 集成
- **独立节点**: `knowledge_retrieval_node` 在工作流中独立运行
- **智能触发**: 基于关键词和意图判断是否启用 RAG
- **上下文注入**: 检索内容自动注入系统提示词

## 📁 项目结构

```
AIchat4.11/
├── backendtest/
│   └── LLM/
│       ├── RAG/                    # RAG 模块(新增)
│       │   ├── __init__.py
│       │   ├── knowledge_base.py   # 知识库管理器
│       │   ├── llm_provider.py     # LLM Provider 抽象层
│       │   ├── generate_summary.py # 摘要生成器
│       │   └── rag_tools.py        # RAG 工具函数
│       ├── nodes.py                # 已添加 knowledge_retrieval_node
│       ├── workflow.py             # 已集成 RAG 节点
│       ├── models.py               # 已添加 RAG 状态字段
│       └── service.py
├── Knowledge-Base/                 # 原始知识库(示例数据)
│   ├── Product-Line-A-Smartwatch-Series/
│   │   ├── SW-2100-Flagship.md
│   │   └── SW-1500-Sport.md
│   └── 2024-Market-Layout/
│       └── East-China-Region.md
├── Knowledge-Base-Chunks/          # 分块后的知识库(自动生成)
├── Knowledge-Base-File-Summary/    # 知识库摘要(自动生成)
│   └── summary.txt
├── tests/
│   └── test_rag_integration.py     # RAG 集成测试
└── run_rag_test.bat                # 快速测试脚本
```

## 🚀 快速开始

### 步骤1: 安装依赖

```bash
pip install aiofiles tiktoken nest-asyncio
```

### 步骤2: 准备知识库

将你的文档放入 `Knowledge-Base/` 目录,支持 Markdown 格式。

示例结构:
```
Knowledge-Base/
├── 产品文档/
│   ├── 产品A.md
│   └── 产品B.md
├── 技术手册/
│   └── API文档.md
└── 业务资料/
    └── 市场报告.md
```

### 步骤3: 生成知识库摘要

```bash
python backendtest/LLM/RAG/generate_summary.py
```

这会:
1. 扫描所有 `.md` 文件
2. 为每个文件生成简洁摘要
3. 大文件自动分块
4. 生成 `summary.txt` 作为"知识地图"

### 步骤4: 运行测试

```bash
# Windows
run_rag_test.bat

# Linux/Mac
python tests/test_rag_integration.py
```

### 步骤5: 启动服务

```bash
# 启动后端
cd backendtest
python api_server.py

# 启动前端(另一个终端)
cd frontendtest
npm run dev
```

## 💡 使用示例

### 示例1: 询问产品规格

**用户**: "SW-2100智能手表的电池续航是多少?"

**工作流程**:
1. `intent_recognition_node` 识别为知识查询
2. `knowledge_retrieval_node` 检测到关键词"智能手表"
3. LLM 分析知识库摘要,推荐检索 `Product-Line-A-Smartwatch-Series/SW-2100-Flagship.md`
4. 检索到完整产品信息
5. 检索内容注入系统提示词
6. LLM 基于检索内容生成回答

**AI 回复**: "SW-2100旗舰智能手表的电池续航表现优秀:
- 典型使用: 72小时(3天)
- 省电模式: 14天
- 充电时间: 约2小时充满
- 电池容量: 500mAh,支持磁吸无线充电"

### 示例2: 市场数据查询

**用户**: "2024年华东地区的市场份额是多少?"

**AI 回复**: "根据2024年市场布局数据,华东地区的市场份额情况如下:
- 华为: 28%
- 小米: 22%
- 我们: 18%
- OPPO: 12%
- 其他: 20%

华东地区是公司核心市场,占总营收的35%。"

### 示例3: 普通对话(不触发 RAG)

**用户**: "你好,今天心情怎么样?"

**工作流程**: 
- 未检测到知识查询关键词
- 跳过 `knowledge_retrieval_node`
- 直接使用 LLM 生成回复

**AI 回复**: "你好!我很好,谢谢关心。有什么可以帮助你的吗?"

## 🔧 配置说明

### 修改知识库路径

编辑 `LLM/RAG/knowledge_base.py`:

```python
def __init__(self, base_path: str = None, summary_file: str = None):
    if base_path is None:
        base_path = "你的知识库路径"
    if summary_file is None:
        summary_file = "你的摘要文件路径"
```

### 调整 RAG 触发条件

编辑 `LLM/nodes.py` 中的 `knowledge_retrieval_node`:

```python
knowledge_keywords = [
    "产品", "规格", "参数",  # 添加你的关键词
    "如何", "怎么", "什么"
]
```

### 更换 LLM Provider

编辑 `LLM/RAG/llm_provider.py`:

```python
provider = UnifiedLLMProvider(
    base_url="https://api.openai.com/v1",
    api_key="your-api-key",
    model="gpt-4"
)
```

## 📊 性能优化建议

1. **知识库大小**: 建议单个文件不超过 5000 tokens
2. **摘要质量**: 定期重新生成摘要以保持准确性
3. **缓存利用**: `generate_summary.py` 会自动缓存,避免重复生成
4. **检索范围**: 尽量检索具体文件而非整个目录,减少 token 消耗

## 🐛 常见问题

### Q1: 摘要生成失败?
**A**: 检查:
- API Key 是否正确
- 网络连接是否正常
- `Knowledge-Base/` 目录是否存在且包含 `.md` 文件

### Q2: RAG 未触发?
**A**: 检查:
- 用户输入是否包含知识查询关键词
- 知识库摘要是否已生成
- 查看控制台日志确认节点执行情况

### Q3: 检索结果不准确?
**A**: 优化:
- 完善知识库文档结构
- 调整 LLM 温度参数(降低可提高准确性)
- 检查知识库摘要质量

## 📝 开发指南

### 添加新的 RAG 工具

在 `LLM/RAG/rag_tools.py` 中添加:

```python
def create_new_tool() -> Dict:
    return {
        "type": "function",
        "function": {
            "name": "new_tool",
            "description": "工具描述",
            "parameters": {...}
        }
    }
```

### 自定义检索逻辑

继承 `KnowledgeBaseManager` 类并重写方法:

```python
class CustomKnowledgeBase(KnowledgeBaseManager):
    async def retrieve_files(self, file_paths: List[str]) -> str:
        # 自定义检索逻辑
        pass
```

## 🎓 学习资源

- **Deep RAG 原理**: 参考 `deep-rag-main/README.md`
- **LangGraph 文档**: https://langchain-ai.github.io/langgraph/
- **RAG 最佳实践**: 保持知识库更新,定期优化摘要

## ✅ 集成检查清单

- [x] 创建 RAG 模块目录结构
- [x] 实现知识库管理器
- [x] 实现 LLM Provider 抽象层
- [x] 实现摘要生成器
- [x] 添加 RAG 检索节点到工作流
- [x] 更新状态模型
- [x] 创建示例知识库
- [x] 编写集成测试
- [x] 创建快速测试脚本

## 📞 技术支持

如有问题,请查看:
1. 控制台日志(详细调试信息)
2. 测试用例(`tests/test_rag_integration.py`)
3. RAG 模块源码(含详细中文注释)

---

**祝使用愉快! 🎉**
