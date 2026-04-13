"""
节点定义
包含 LangGraph 对话引擎中的所有处理节点
"""
from langchain_core.messages import AIMessage, SystemMessage

# 修复导入路径问题
try:
    from config import qwen_base_url, qwen_api_key
except ImportError:
    from backendtest.config import qwen_base_url, qwen_api_key


def process_input_node(state: dict) -> dict:
    """
    处理用户输入节点
    对用户消息进行预处理和分类
    """
    print(f"📥 收到用户消息：{state['user_input']}")
    
    # 这里可以添加输入验证、过滤等逻辑
    user_input = state['user_input'].strip()
    
    if not user_input:
        return {
            "ai_response": "请输入有效内容",
            "needs_human_review": False
        }
    
    # 默认不需要人工审核
    return {
        "needs_human_review": False
    }


def llm_response_node(state: dict) -> dict:
    """
    LLM 响应节点（支持工具调用 + RAG 知识库）
    调用通义千问 API 生成回复，支持自动识别并调用工具
    如果使用了 RAG 检索，会将检索内容注入到系统提示词中
    """
    from langchain_openai import ChatOpenAI
    from .tools import AVAILABLE_TOOLS, TOOLS_DESCRIPTION
    
    print("🤖 LLM 正在思考...")
    
    # 创建 LLM 实例
    llm = ChatOpenAI(
        model="qwen-plus",
        base_url=qwen_base_url,
        api_key=qwen_api_key,
        temperature=0.5,
    )
    
    # 绑定工具函数
    llm_with_tools = llm.bind_tools(AVAILABLE_TOOLS)
    
    # 检查是否使用了 RAG 检索
    rag_content = state.get('rag_retrieved_content', '')
    rag_used = state.get('rag_used', False)
    
    # 构建系统提示词
    if rag_used and rag_content:
        # 如果使用了 RAG,将检索内容注入到提示词中
        system_prompt = f"""你是一个专业、冷静、用词犀利的 AI 助手。
请用简洁清晰的中文回答用户问题。

{TOOLS_DESCRIPTION}

## 知识库检索结果
以下是从知识库中检索到的相关内容，请基于这些内容回答用户问题：

{rag_content[:10000]}  # 限制长度,避免超出 token 限制

⚠️ 重要规则：
1. **优先使用知识库检索结果**来回答问题
2. 不要向用户展示你的内部分析过程（如情感分析、意图识别、关键词提取等）
3. 不要输出结构化数据（如 JSON、字典、列表等）
4. 直接给出自然、流畅的回复，就像正常对话一样
5. 如果调用了工具，只使用工具返回的结果来组织回复，不要重复工具的原始输出格式
6. 如果知识库中没有相关信息，请诚实说明"""
    else:
        # 未使用 RAG,使用原有提示词
        system_prompt = f"""你是一个专业、冷静、用词犀利的 AI 助手。
请用简洁清晰的中文回答用户问题。

{TOOLS_DESCRIPTION}

当用户的问题可以通过上述工具解决时，请优先使用对应的工具。
如果涉及专业知识，请基于事实回答；如果不了解，请诚实说明。
始终保持礼貌和专业的语气。

⚠️ 重要规则：
1. 不要向用户展示你的内部分析过程（如情感分析、意图识别、关键词提取等）
2. 不要输出结构化数据（如 JSON、字典、列表等）
3. 直接给出自然、流畅的回复，就像正常对话一样
4. 如果调用了工具，只使用工具返回的结果来组织回复，不要重复工具的原始输出格式"""

    # 构建消息历史
    messages = state['messages']
    enhanced_messages = [SystemMessage(content=system_prompt)] + messages
    
    try:
        # 调用带工具的 LLM
        response = llm_with_tools.invoke(enhanced_messages)
        
        # 检查是否需要调用工具
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print("🔧 检测到工具调用意图")
            
            # 导入所有工具函数
            from .tools import (
                get_current_time, get_weekday, get_date_info,
                calculate, get_weather, get_weather_forecast,
                analyze_sentiment, analyze_emotion, analyze_intent,
                extract_keywords, extract_entities
            )
            
            # 工具函数映射表
            tool_functions = {
                'get_current_time': get_current_time,
                'get_weekday': get_weekday,
                'get_date_info': get_date_info,
                'calculate': calculate,
                'get_weather': get_weather,
                'get_weather_forecast': get_weather_forecast,
                'analyze_sentiment': analyze_sentiment,
                'analyze_emotion': analyze_emotion,
                'analyze_intent': analyze_intent,
                'extract_keywords': extract_keywords,
                'extract_entities': extract_entities,
            }
            
            tool_results = []
            
            # 执行每个工具调用
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call.get('args', {})
                
                print(f"  📦 调用工具：{tool_name}, 参数：{tool_args}")
                
                # 获取对应的工具函数
                tool_func = tool_functions.get(tool_name)
                
                if tool_func:
                    try:
                        # 调用工具
                        result = tool_func(**tool_args)
                        tool_results.append(result)
                        print(f"  ✅ 工具返回：{result[:100]}..." if len(result) > 100 else f"  ✅ 工具返回：{result}")
                    except Exception as e:
                        error_result = f"❌ 工具 {tool_name} 执行失败：{str(e)}"
                        tool_results.append(error_result)
                        print(f"  ❌ 工具执行错误：{e}")
                else:
                    tool_results.append(f"❌ 未找到工具：{tool_name}")
            
            # 整合工具结果
            if tool_results:
                ai_content = "\n\n".join(tool_results)
                return {
                    "messages": [AIMessage(content=ai_content)],
                    "ai_response": ai_content,
                    "needs_human_review": False
                }
        
        # 无需工具调用，直接返回 LLM 回复
        return {
            "messages": [response],
            "ai_response": response.content,
            "needs_human_review": False
        }
        
    except Exception as e:
        error_msg = f"抱歉，发生错误：{str(e)}"
        return {
            "ai_response": error_msg,
            "needs_human_review": False
        }


def review_decision_node(state: dict) -> dict:
    """
    审核决策节点
    判断是否需要人工审核
    （可扩展：检测敏感词、高风险操作等）
    """
    # 示例：检测特定关键词
    sensitive_keywords = ["删除", "清空", "重置", "管理员"]
    
    has_sensitive = any(kw in state['user_input'] for kw in sensitive_keywords)
    
    if has_sensitive:
        print("⚠️ 检测到敏感操作，需要人工审核")
        return {"needs_human_review": True}
    
    return {"needs_human_review": False}


def human_review_node(state: dict) -> dict:
    """
    人工审核节点
    （实际应用中可以暂停流程，等待人工确认）
    """
    print("👤 等待人工审核...")
    
    # 这里是占位逻辑，实际应用可以：
    # 1. 发送通知给管理员
    # 2. 将请求加入审核队列
    # 3. 暂停流程并返回“等待审核”状态
    
    return {
        "ai_response": "您的请求已提交，等待管理员审核",
        "needs_human_review": False
    }


def sentiment_analysis_node(state: dict) -> dict:
    """
    情感分析节点 - 独立的情感倾向分析
    """
    user_input = state.get('user_input', '')
    
    # 快速判断: 跳过太短或明显的闲聊
    if not user_input or len(user_input.strip()) < 5:
        return {"sentiment_result": {"analyzed": False, "reason": "文本过短"}}
    
    # 检测是否需要详细分析(包含负面/投诉关键词)
    negative_keywords = ["投诉", "差", "坏", "烂", "失望", "生气", "愤怒", "不满", "问题", "故障"]
    need_deep_analysis = any(kw in user_input for kw in negative_keywords)
    
    if not need_deep_analysis:
        print(f"💬 普通对话,跳过详细情感分析")
        return {"sentiment_result": {"analyzed": False, "reason": "普通对话"}}
    
    try:
        from .emotion.sentiment_analyzer import SentimentAnalyzer
        
        print("📊 开始情感分析...")
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze(user_input)
        
        print(f"✅ 情感分析完成: {result.get('label_cn')}")
        
        return {
            "sentiment_result": {
                "analyzed": True,
                "raw_text": user_input[:100],
                "label": result.get('label'),
                "label_cn": result.get('label_cn'),
                "score": result.get('score'),
                "emoji": result.get('emoji')
            }
        }
    
    except Exception as e:
        print(f"⚠️ 情感分析失败: {str(e)}")
        return {"sentiment_result": {"analyzed": False, "error": str(e)}}


def intent_recognition_node(state: dict) -> dict:
    """
    意图识别节点 - 独立的用户意图分析
    """
    user_input = state.get('user_input', '')
    
    # 快速判断
    if not user_input or len(user_input.strip()) < 5:
        return {"intent_result": {"analyzed": False, "reason": "文本过短"}}
    
    try:
        from .intent.intent_analyzer import IntentAnalyzer
        
        print("🎯 开始意图识别...")
        analyzer = IntentAnalyzer()
        result = analyzer.analyze(user_input)
        
        print(f"✅ 意图识别完成: {result.get('intent')}")
        
        return {
            "intent_result": {
                "analyzed": True,
                "raw_text": user_input[:100],
                "intent": result.get('intent'),
                "confidence": result.get('confidence'),
                "action_needed": result.get('action_needed'),
                "priority": result.get('priority')
            }
        }
    
    except Exception as e:
        print(f"⚠️ 意图识别失败: {str(e)}")
        return {"intent_result": {"analyzed": False, "error": str(e)}}


async def knowledge_retrieval_node(state: dict) -> dict:
    """
    知识库检索节点 - 根据用户问题从知识库检索相关内容
    
    工作流程:
    1. 检查用户输入是否包含知识查询关键词
    2. 如果匹配,调用 LLM 判断需要检索哪些文件
    3. 执行检索并返回内容
    
    Args:
        state: 对话状态
        
    Returns:
        包含检索内容的状态更新
    """
    user_input = state.get('user_input', '')
    
    # 快速判断: 跳过明显不需要知识库的问题
    knowledge_keywords = [
        "产品", "规格", "参数", "技术", "文档", "手册",
        "功能", "特性", "型号", "版本", "配置",
        "市场", "销售", "供应商", "合作",
        "如何", "怎么", "什么", "哪些"  # 疑问词
    ]
    
    need_knowledge = any(kw in user_input for kw in knowledge_keywords)
    
    if not need_knowledge:
        print(f"💬 普通对话,跳过知识库检索")
        return {
            "rag_retrieved_content": "",
            "rag_used": False
        }
    
    try:
        from .RAG.rag_tools import retrieve_knowledge, get_knowledge_summary
        from langchain_openai import ChatOpenAI
        from config import qwen_base_url, qwen_api_key
        
        print("📚 开始知识库检索...")
        
        # 获取知识库摘要(知识地图)
        summary = get_knowledge_summary()
        
        # 使用 LLM 判断需要检索哪些文件
        llm = ChatOpenAI(
            model="qwen-plus",
            base_url=qwen_base_url,
            api_key=qwen_api_key,
            temperature=0.3,
        )
        
        prompt = f"""你是一个智能知识库检索助手。根据用户问题和知识库结构,判断需要检索哪些文件。

## 知识库结构
{summary}

## 用户问题
{user_input}

## 任务
请分析用户问题,从知识库中选择最相关的文件路径。可以检索:
- 单个文件: ["Product-Line-A/SW-2100.md"]
- 整个目录: ["Product-Line-A/"]
- 多个路径: ["Product-Line-A/", "2024-Market-Layout/"]
- 所有文件: ["/"]

## 输出格式
只输出 JSON 数组,不要其他内容。例如:
["Product-Line-A/SW-2100.md"]

如果没有相关文件,输出空数组 []。
"""
        
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=prompt)])
        
        # 解析 LLM 返回的文件路径
        import json
        try:
            file_paths = json.loads(response.content.strip())
        except:
            # 如果解析失败,尝试提取 JSON 部分
            import re
            match = re.search(r'\[.*?\]', response.content, re.DOTALL)
            if match:
                file_paths = json.loads(match.group())
            else:
                file_paths = []
        
        if not file_paths:
            print(f"⚠️  LLM 未推荐任何文件,跳过检索")
            return {
                "rag_retrieved_content": "",
                "rag_used": False
            }
        
        print(f"🔍 LLM 推荐检索: {file_paths}")
        
        # 执行检索
        content = await retrieve_knowledge(file_paths)
        
        print(f"✅ 知识库检索完成,共 {len(content)} 字符")
        
        return {
            "rag_retrieved_content": content,
            "rag_used": True
        }
    
    except Exception as e:
        print(f"⚠️ 知识库检索失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "rag_retrieved_content": "",
            "rag_used": False,
            "rag_error": str(e)
        }
