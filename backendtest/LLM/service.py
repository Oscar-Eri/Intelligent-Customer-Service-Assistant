"""    
服务类
LangGraph 聊天服务的封装
"""
from typing import List, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage
from .workflow import build_chat_workflow
from .Memory import MemoryManager, create_memory_manager


class LangGraphChatService:
    """
    LangGraph 聊天服务
    封装工作流，提供简单接口
    """
    
    # 全局系统提示词（在所有对话前添加）
    SYSTEM_PROMPT = """你是一个专业、冷静、用词犀利的 AI 助手。
    请用简洁清晰的中文回答用户问题。
    如果涉及专业知识，请基于事实回答；如果不了解，请诚实说明。
    始终保持礼貌和专业的语气。"""
    
    def __init__(self, 
                 max_tokens: int = 4000, 
                 max_messages: int = 10,
                 enable_memory_persistence: bool = True,
                 enable_contextatlas: bool = True):
        """
        初始化聊天服务
        
        Args:
            max_tokens: 最大 token 数
            max_messages: 最大对话消息数
            enable_memory_persistence: 是否启用记忆持久化
            enable_contextatlas: 是否启用 ContextAtlas 项目记忆
        """
        self.app = build_chat_workflow()
        
        # 使用 MemoryManager 管理对话历史
        if enable_memory_persistence:
            from pathlib import Path
            current_dir = Path(__file__).parent
            date_folder = current_dir / "Memory" / "Date"
            
            self.memory = create_memory_manager(
                max_tokens=max_tokens,
                max_messages=max_messages,
                date_folder=str(date_folder),
                enable_summary=True
            )
        else:
            self.memory = create_memory_manager(
                max_tokens=max_tokens,
                max_messages=max_messages
            )
        
        # 集成 ContextAtlas 适配器（可选）
        self.contextatlas = None
        if enable_contextatlas:
            try:
                from .Memory import create_contextatlas_adapter
                current_dir = Path(__file__).parent
                repo_path = str(current_dir.parent.parent.parent / "AIchat")
                
                self.contextatlas = create_contextatlas_adapter(repo_path=repo_path)
                print("✅ ContextAtlas 已集成")
            except Exception as e:
                print(f"⚠️ ContextAtlas 集成失败: {e}")
                self.contextatlas = None
    
    async def chat(self, user_message: str) -> str:
        """
        处理用户消息并返回 AI 回复
        
        Args:
            user_message: 用户输入
            
        Returns:
            AI 回复内容
        """
        # 添加用户消息到记忆
        self.memory.add_user_message(user_message)
        
        # 获取记忆用于 LLM（包含历史总结）
        messages = self.memory.get_messages_for_llm()
        
        # 如果有 ContextAtlas，注入项目上下文
        if self.contextatlas and self.contextatlas.available:
            project_context = self.contextatlas.get_project_context()
            if project_context:
                # 在系统提示后添加项目上下文
                from langchain_core.messages import SystemMessage
                context_msg = SystemMessage(
                    content=f"【项目背景知识】\n{project_context}\n"
                )
                messages.insert(0, context_msg)
        
        # 运行工作流
        result = await self.app.ainvoke({
            "messages": messages,
            "user_input": user_message,
            "ai_response": "",
            "needs_human_review": False,
            "sentiment_result": {}  # 初始化情感分析结果
        })
        
        # 保存 AI 回复到记忆
        ai_response = result["ai_response"]
        self.memory.add_ai_message(ai_response)
        
        # 保存增强分析结果到文件（情感+意图+关键词+实体）
        sentiment_result = result.get("sentiment_result", {})
        intent_result = result.get("intent_result", {})
        keywords_result = result.get("keywords_result", {})
        entities_result = result.get("entities_result", {})
        
        if sentiment_result and sentiment_result.get("analyzed"):
            await self._save_sentiment_to_memory(
                sentiment_result=sentiment_result,
                intent_result=intent_result,
                keywords_result=keywords_result,
                entities_result=entities_result
            )
        
        # 生成总结并保存到文件
        await self.memory.generate_summary(force=True)
        
        # 清理内存中的消息，只保留最近 10 条
        if self.memory.get_message_count() > 10:
            excess_count = self.memory.get_message_count() - 10
            self.memory.remove_oldest_messages(excess_count)
        
        return ai_response
    
    def clear_history(self):
        """清空对话历史"""
        self.memory.clear()
    
    def get_history(self):
        """获取对话历史"""
        return self.memory.get_messages()
    
    async def chat_stream(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        流式处理用户消息并生成 AI 回复（支持完整功能：情感分析、意图识别等）
        
        Args:
            user_message: 用户输入
            
        Yields:
            AI 回复的文本片段
        """
        print(f"\n📥 收到用户消息：{user_message[:50]}...")
        
        # 添加用户消息到记忆
        self.memory.add_user_message(user_message)
        print(f"✅ 用户消息已添加到记忆")
        
        # 获取记忆用于 LLM（包含历史总结）
        messages = self.memory.get_messages_for_llm()
        print(f"📚 准备发送给 LLM 的消息数：{len(messages)}")
        
        # 如果有 ContextAtlas，注入项目上下文
        if self.contextatlas and self.contextatlas.available:
            project_context = self.contextatlas.get_project_context()
            if project_context:
                from langchain_core.messages import SystemMessage
                context_msg = SystemMessage(
                    content=f"【项目背景知识】\n{project_context}\n"
                )
                messages.insert(0, context_msg)
                print(f"✅ 已注入 ContextAtlas 上下文")
        
        print(f"🤖 开始流式调用 LangGraph 工作流...")
        
        # 使用 LangGraph 工作流的流式执行
        full_response = ""
        sentiment_result = {}
        intent_result = {}
        keywords_result = {}
        entities_result = {}
        
        try:
            # 使用 astream 方法流式执行工作流
            async for event in self.app.astream({
                "messages": messages,
                "user_input": user_message,
                "ai_response": "",
                "needs_human_review": False,
                "sentiment_result": {}
            }):
                # 处理工作流中的事件
                for node_name, node_output in event.items():
                    print(f"🔍 节点执行: {node_name}")
                    
                    # 如果是 llm_response 节点，提取流式内容
                    if node_name == "llm_response" and isinstance(node_output, dict):
                        # 检查是否有 ai_response
                        if "ai_response" in node_output and node_output["ai_response"]:
                            # 这里我们只能在工作流完成后获取完整响应
                            # 如果需要真正的流式，需要在 nodes.py 中修改
                            pass
                    
                    # 保存情感分析结果
                    if "sentiment_result" in node_output and node_output["sentiment_result"]:
                        sentiment_result = node_output["sentiment_result"]
                    if "intent_result" in node_output and node_output["intent_result"]:
                        intent_result = node_output["intent_result"]
                    if "keywords_result" in node_output and node_output["keywords_result"]:
                        keywords_result = node_output["keywords_result"]
                    if "entities_result" in node_output and node_output["entities_result"]:
                        entities_result = node_output["entities_result"]
            
            # 注意：LangGraph 的 astream 不支持真正的逐字流式输出
            # 我们需要改用普通模式，但保持异步特性
            # 重新使用 ainvoke 获取完整结果
            result = await self.app.ainvoke({
                "messages": messages,
                "user_input": user_message,
                "ai_response": "",
                "needs_human_review": False,
                "sentiment_result": {}
            })
            
            full_response = result.get("ai_response", "")
            sentiment_result = result.get("sentiment_result", {})
            intent_result = result.get("intent_result", {})
            keywords_result = result.get("keywords_result", {})
            entities_result = result.get("entities_result", {})
            
            print(f"✅ LangGraph 工作流执行完成，共 {len(full_response)} 字符")
            
            # 模拟流式输出（逐字发送）
            chunk_size = 20  # 每次发送 20 个字符(从 10 增加到 20,减少请求次数)
            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i:i+chunk_size]
                yield chunk
                # 小延迟，模拟打字效果(从 0.05 降到 0.02)
                import asyncio
                await asyncio.sleep(0.02)
            
            print(f"✅ 流式输出完成")
            
            # 保存 AI 回复到记忆
            self.memory.add_ai_message(full_response)
            print(f"✅ AI 回复已保存到记忆")
            
            # 立即保存到磁盘文件
            self.memory._save_today_memory()
            print(f"💾 记忆已保存到磁盘文件")
            
            # 保存增强分析结果
            if sentiment_result and sentiment_result.get("analyzed"):
                await self._save_sentiment_to_memory(
                    sentiment_result=sentiment_result,
                    intent_result=intent_result,
                    keywords_result=keywords_result,
                    entities_result=entities_result
                )
            
            # 生成总结并保存到文件
            await self.memory.generate_summary(force=True)
            
            # 清理内存中的消息，只保留最近 10 条
            if self.memory.get_message_count() > 10:
                excess_count = self.memory.get_message_count() - 10
                self.memory.remove_oldest_messages(excess_count)
            
        except Exception as e:
            print(f"❌ LangGraph 工作流执行失败：{str(e)}")
            import traceback
            traceback.print_exc()
            error_msg = f"抱歉，发生错误：{str(e)}"
            yield error_msg
    
    async def _save_sentiment_to_memory(self, sentiment_result: dict, intent_result: dict = None, keywords_result: dict = None, entities_result: dict = None):
        """
        将增强分析结果保存到记忆系统（情感+意图+关键词+实体）
        
        Args:
            sentiment_result: 情感分析结果字典
            intent_result: 意图识别结果字典（可选）
            keywords_result: 关键词提取结果字典（可选）
            entities_result: 实体抽取结果字典（可选）
        """
        try:
            from datetime import datetime
            import json
            from pathlib import Path
            
            # 获取当前模块所在目录
            current_dir = Path(__file__).parent
            sentiment_log_file = current_dir / "Memory" / "Date" / "sentiment_log.json"
            
            # 读取现有日志
            sentiment_history = []
            if sentiment_log_file.exists():
                with open(sentiment_log_file, 'r', encoding='utf-8') as f:
                    try:
                        sentiment_history = json.load(f)
                    except:
                        sentiment_history = []
            
            # 添加新的增强分析记录
            record = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text_preview": sentiment_result.get("raw_text", "")[:50],
                "sentiment_label": sentiment_result.get("sentiment_label", "未知"),
                "sentiment_score": sentiment_result.get("sentiment_score", 0),
                "pos_count": sentiment_result.get("pos_count", 0),
                "neg_count": sentiment_result.get("neg_count", 0),
                # 新增字段
                "intent_result": intent_result or {"analyzed": False},
                "keywords_result": keywords_result or {"analyzed": False},
                "entities_result": entities_result or {"analyzed": False}
            }
            sentiment_history.append(record)
            
            # 只保留最近 100 条记录
            if len(sentiment_history) > 100:
                sentiment_history = sentiment_history[-100:]
            
            # 保存到文件
            with open(sentiment_log_file, 'w', encoding='utf-8') as f:
                json.dump(sentiment_history, f, ensure_ascii=False, indent=2)
            
            print(f"💾 增强分析结果已保存")
            
        except Exception as e:
            print(f"⚠️ 保存增强分析结果失败: {str(e)}")
