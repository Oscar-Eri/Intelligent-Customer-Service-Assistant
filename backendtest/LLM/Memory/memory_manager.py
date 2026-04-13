"""
记忆管理模块
负责管理对话历史的存储、检索、清理和 token 控制
支持长期记忆的保存和加载（对话总结）
"""
import json
import asyncio
from pathlib import Path
from typing import List, Optional, Dict
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI


class MemoryManager:
    """
    记忆管理器
    管理对话历史的存储、检索、清理和 token 控制
    支持长期记忆的保存和加载
    """

    def __init__(self,
                 max_tokens: int = 4000,
                 max_messages: Optional[int] = None,
                 date_folder: Optional[str] = None,
                 enable_summary: bool = True):
        """
        初始化记忆管理器
        
        Args:
            max_tokens: 最大 token 数限制，超过会自动截断（默认 4000）
            max_messages: 最大消息数量限制（可选，不设置则只按 token 数控制）
            date_folder: 日期文件夹路径，用于保存和加载按日期分类的记忆
            enable_summary: 是否启用对话总结功能
        """
        self._messages: List[BaseMessage] = []
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        # 注意：Path 已在文件顶部导入，这里直接使用
        self.date_folder = Path(date_folder) if date_folder else None
        self.enable_summary = enable_summary

        # 长期记忆：对话总结
        self._conversation_summary: str = ""
        self._permanent_summary: str = ""  # 永久总结

        # 当前日期文件
        self._current_date_file: Optional[Path] = None
        self._current_date_str: str = ""

        # LLM 配置（用于生成总结）
        try:
            from backend.config import qwen_base_url, qwen_api_key
        except ImportError:
            # 如果不在 backendtest 包中运行，从本地 config 导入
            try:
                from ..config import qwen_base_url, qwen_api_key
            except ImportError:
                # 最后的备用方案：直接导入
                import sys
                # Path 已在文件顶部导入，不需要再次导入
                backend_dir = Path(__file__).parent.parent.parent
                if str(backend_dir) not in sys.path:
                    sys.path.insert(0, str(backend_dir))
                from config import qwen_base_url, qwen_api_key

        self.llm = ChatOpenAI(
            model="qwen-plus",
            base_url=qwen_base_url,
            api_key=qwen_api_key,
            temperature=0.3,  # 较低的温度让总结更稳定
        )

        # 启动时加载日期文件夹和永久总结
        if self.date_folder:
            self._init_date_folder()
            self.load_permanent_summary()

    def add_message(self, message: BaseMessage) -> None:
        """
        添加消息到记忆中
        
        Args:
            message: 要添加的消息（HumanMessage 或 AIMessage）
        """
        self._messages.append(message)
        # 添加后检查是否需要清理
        self._trim_if_needed()

    def add_user_message(self, content: str) -> None:
        """
        添加用户消息
        
        Args:
            content: 用户消息内容
        """
        self.add_message(HumanMessage(content=content))

    def add_ai_message(self, content: str) -> None:
        """
        添加 AI 回复
        
        Args:
            content: AI 回复内容
        """
        self.add_message(AIMessage(content=content))

    def get_messages(self) -> List[BaseMessage]:
        """
        获取所有消息
        
        Returns:
            消息列表的副本
        """
        return self._messages.copy()

    def get_messages_for_llm(self, include_summary: bool = True, include_permanent: bool = True) -> List[BaseMessage]:
        """
        获取用于传递给 LLM 的消息（已根据 token 限制优化）
        
        Args:
            include_summary: 是否包含今天的对话总结
            include_permanent: 是否包含永久总结
            
        Returns:
            优化后的消息列表
        """
        messages = self.get_messages()

        # 添加永久总结（在所有消息之前）
        if include_permanent and self._permanent_summary:
            permanent_message = HumanMessage(
                content=f"【历史重要内容总结】\n{self._permanent_summary}\n\n以上是之前周期的重要信息，请参考。"
            )
            messages.insert(0, permanent_message)

        # 添加今天的总结（在永久总结之后，当前消息之前）
        if include_summary and self._conversation_summary:
            today_message = HumanMessage(
                content=f"【今天对话的总结】\n{self._conversation_summary}\n\n请基于以上背景继续对话。"
            )
            # 插入到永久总结之后，其他消息之前
            insert_index = 1 if include_permanent and self._permanent_summary else 0
            messages.insert(insert_index, today_message)

        return messages

    def clear(self) -> None:
        """清空当前对话历史（但不删除长期记忆）"""
        self._messages = []

    def clear_all(self) -> None:
        """清空所有记忆（包括今天的文件和永久总结）"""
        self.clear()
        self._conversation_summary = ""
        self._permanent_summary = ""
        # 可以选择删除文件
        # if self._current_date_file and self._current_date_file.exists():
        #     self._current_date_file.unlink()
        if self.date_folder:
            self._save_today_memory()  # 保存清空的今天记忆
            self._save_permanent_summary([])  # 保存清空的永久总结

    def get_message_count(self) -> int:
        """
        获取消息数量
        
        Returns:
            消息总数
        """
        return len(self._messages)

    def estimate_tokens(self) -> int:
        """
        估算当前记忆的 token 数
        
        Returns:
            估算的 token 总数（简单估算：每 4 个字符约 1 个 token）
        """
        total_chars = sum(len(msg.content) for msg in self._messages)
        return total_chars // 4

    def _trim_if_needed(self) -> None:
        """
        如果超出限制，清理记忆
        优先保留最新的消息
        """
        if not self._messages:
            return

        # 按消息数量清理
        if self.max_messages and len(self._messages) > self.max_messages:
            # 保留最新的 max_messages 条
            self._messages = self._messages[-self.max_messages:]
            return

        # 按 token 数清理
        if self.estimate_tokens() > self.max_tokens:
            # 从最旧的消息开始删除，直到满足限制
            while len(self._messages) > 2 and self.estimate_tokens() > self.max_tokens:
                # 至少保留最新的 2 条消息（一问一答）
                self._messages.pop(0)

    def remove_oldest_messages(self, count: int = 1) -> None:
        """
        删除最旧的 N 条消息
        
        Args:
            count: 要删除的消息数量
        """
        if count > 0 and count <= len(self._messages):
            self._messages = self._messages[count:]

    def get_last_message(self) -> Optional[BaseMessage]:
        """
        获取最后一条消息
        
        Returns:
            最后一条消息，如果为空则返回 None
        """
        return self._messages[-1] if self._messages else None

    def get_conversation_summary(self) -> str:
        """
        获取对话摘要（用于调试或显示）
        
        Returns:
            对话摘要字符串
        """
        if not self._messages:
            return "暂无对话历史"

        summary_lines = [f"共 {len(self._messages)} 条消息"]
        for i, msg in enumerate(self._messages[-5:], 1):  # 只显示最后 5 条
            role = "用户" if isinstance(msg, HumanMessage) else "AI"
            content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            summary_lines.append(f"{i}. {role}: {content}")

        return "\n".join(summary_lines)

    def _init_date_folder(self) -> None:
        """
        初始化日期文件夹，创建今天的文件
        """
        if not self.date_folder:
            return

        # 确保目录存在
        self.date_folder.mkdir(parents=True, exist_ok=True)

        # 获取今天日期
        from datetime import datetime
        today = datetime.now()
        self._current_date_str = today.strftime("%Y%m%d")
        self._current_date_file = self.date_folder / f"{self._current_date_str}.json"

        print(f"📅 当前日期文件：{self._current_date_file.name}")

        # 加载今天的记忆（如果存在）
        self._load_today_memory()

        # 清理超过 7 天的文件
        self._cleanup_old_files()
        
        # 安排异步任务检查并生成周期总结
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._check_and_generate_periodic_summary())
            else:
                # 如果循环没有运行，创建一个新线程来运行
                import threading
                def run_async_task():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(self._check_and_generate_periodic_summary())
                    new_loop.close()
                thread = threading.Thread(target=run_async_task, daemon=True)
                thread.start()
        except RuntimeError:
            # 如果没有事件循环，创建一个新线程来运行
            import threading
            def run_async_task():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(self._check_and_generate_periodic_summary())
                new_loop.close()
            thread = threading.Thread(target=run_async_task, daemon=True)
            thread.start()

    def _get_date_files(self) -> List[Path]:
        """
        获取所有日期文件（按日期排序）
        
        Returns:
            日期文件列表，最新的在前
        """
        if not self.date_folder or not self.date_folder.exists():
            return []

        files = list(self.date_folder.glob("*.json"))
        # 排除永久总结文件和情感分析日志文件
        files = [f for f in files if f.name not in ["permanent_summary.json", "sentiment_log.json"]]
        # 按文件名（日期）排序，最新的在前
        files.sort(key=lambda x: x.stem, reverse=True)
        return files

    def _cleanup_old_files(self) -> None:
        """
        清理超过 7 天的文件，只保留最近 7 天
        """
        files = self._get_date_files()

        # 保留最近 7 个文件
        if len(files) > 7:
            for old_file in files[7:]:
                try:
                    old_file.unlink()
                    print(f"🗑️ 已删除过期文件：{old_file.name}")
                except Exception as e:
                    print(f"⚠️ 删除文件失败：{e}")

    def _load_today_memory(self) -> None:
        """
        加载今天的记忆（智能加载：AI 总结 + 最近对话）
        1. 读取完整历史
        2. 如果历史较长，由 AI生成总结
        3. 只加载总结和最近 5 轮对话到内存
        """
        if not self._current_date_file or not self._current_date_file.exists():
            print("ℹ️ 今天是新的一天，将创建新的记忆文件")
            self._conversation_summary = ""
            return
            
        try:
            # 检查文件是否为空
            if self._current_date_file.stat().st_size == 0:
                print(f"⚠️ 文件 {self._current_date_file.name} 为空，将重新创建")
                self._conversation_summary = ""
                return
                
            with open(self._current_date_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON 文件 {self._current_date_file.name} 格式错误：{e}")
                    print("ℹ️ 将尝试从备份恢复或创建新文件")
                    # 可以选择备份损坏的文件
                    backup_file = self._current_date_file.with_suffix('.json.corrupt')
                    self._current_date_file.rename(backup_file)
                    print(f"✅ 已备份损坏文件到：{backup_file.name}")
                    self._conversation_summary = ""
                    return
                
            # 获取对话历史
            conversation_history = data.get("conversation_history", [])
            existing_summary = data.get("summary", "")
                
            print(f"📖 检测到 {len(conversation_history)} 条历史对话")
                    
            if not conversation_history:
                self._conversation_summary = existing_summary
                print(f"✅ 已加载今天的记忆：总结 {len(self._conversation_summary)} 字")
                return
                    
            # 如果已有总结且历史对话不多于 10 条，直接使用
            if existing_summary and len(conversation_history) <= 10:
                self._conversation_summary = existing_summary
                # 加载最近的对话到内存
                self._load_recent_messages(conversation_history, limit=10)
                print(f"✅ 已加载今天的记忆：{len(self._messages)} 条对话，总结 {len(self._conversation_summary)} 字")
                return
                    
            # 如果历史对话很多，需要重新生成总结
            if len(conversation_history) > 10:
                print(f"🤖 正在为 {len(conversation_history)} 条历史对话生成智能总结...")
                
                # 异步生成总结（在同步方法中安全地调用异步方法）
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果事件循环已在运行，使用现有总结，不阻塞
                        print("⚠️ 事件循环运行中，跳过重新生成总结，使用现有总结")
                        self._conversation_summary = existing_summary
                    else:
                        # 事件循环未运行，可以安全调用
                        new_summary = loop.run_until_complete(
                            self._generate_summary_from_history(conversation_history)
                        )
                        if new_summary:
                            self._conversation_summary = new_summary
                            print(f"✅ 已生成智能总结：{len(new_summary)} 字")
                        else:
                            self._conversation_summary = existing_summary
                except RuntimeError:
                    # 没有事件循环，创建新的
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        new_summary = new_loop.run_until_complete(
                            self._generate_summary_from_history(conversation_history)
                        )
                        if new_summary:
                            self._conversation_summary = new_summary
                            print(f"✅ 已生成智能总结：{len(new_summary)} 字")
                        else:
                            self._conversation_summary = existing_summary
                    finally:
                        new_loop.close()
            else:
                self._conversation_summary = existing_summary
                    
            # 加载最近的对话到内存（最多 10 条）
            self._load_recent_messages(conversation_history, limit=10)
            print(f"✅ 已加载今天的记忆：{len(self._messages)} 条对话，总结 {len(self._conversation_summary)} 字")
                    
        except Exception as e:
            print(f"⚠️ 加载今天记忆失败：{e}")
            import traceback
            traceback.print_exc()
            self._conversation_summary = ""

    def _load_recent_messages(self, conversation_history: list, limit: int = 10) -> None:
        """
        从对话历史中加载最近的消息到内存
        
        Args:
            conversation_history: 完整的对话历史列表
            limit: 最多加载多少条消息
        """
        self._messages = []

        # 取最近的 limit 条对话
        recent_history = conversation_history[-limit:] if len(conversation_history) > limit else conversation_history

        for msg_data in recent_history:
            role = msg_data.get("role", "")
            content = msg_data.get("content", "")

            if role == "user":
                self._messages.append(HumanMessage(content=content))
            elif role == "assistant":
                self._messages.append(AIMessage(content=content))

    async def _generate_summary_from_history(self, conversation_history: list) -> str:
        """
        从完整历史生成智能总结
        
        Args:
            conversation_history: 完整的对话历史列表
            
        Returns:
            生成的总结文本
        """
        try:
            # 构建历史对话文本
            history_text = ""
            for msg in conversation_history:
                role = "用户" if msg.get("role") == "user" else "AI"
                content = msg.get("content", "")
                history_text += f"{role}: {content}\n"

            prompt = f"""请总结以下完整对话历史的关键信息，提取重要事实、决定、待办事项等：

{history_text}

请用简洁的中文总结（300 字以内），直接输出总结内容，不要其他说明："""

            # 调用 LLM 生成总结
            response = await self.llm.ainvoke(prompt)
            summary = response.content.strip()

            # 更新保存到文件
            if summary:
                self._conversation_summary = summary
                self._save_today_memory()

            return summary

        except Exception as e:
            print(f"⚠️ 生成历史总结失败：{e}")
            return ""

    async def generate_summary(self, force: bool = False) -> str:
        """
        生成当前对话的总结并保存到今天的文件
        
        Args:
            force: 是否强制生成（即使消息很少）
            
        Returns:
            生成的总结文本
        """
        if not self.enable_summary:
            return ""

        # 如果消息太少，不生成总结
        if len(self._messages) < 4 and not force:
            return self._conversation_summary

        try:
            # 构建总结提示词
            conversation_text = ""
            for msg in self._messages:
                role = "用户" if isinstance(msg, HumanMessage) else "AI"
                conversation_text += f"{role}: {msg.content}\n"

            prompt = f"""请总结以下对话的关键信息，提取重要事实、决定、待办事项等：

{conversation_text}

请用简洁的中文总结（200 字以内），直接输出总结内容，不要其他说明："""

            # 异步调用 LLM
            response = await self.llm.ainvoke(prompt)
            summary = response.content.strip()

            # 更新今天的记忆
            if summary:
                self._conversation_summary = summary
                # 自动保存到今天的文件
                self._save_today_memory()

                # 检查是否需要生成周期总结（每 7 天）
                await self._check_and_generate_periodic_summary()

            return summary

        except Exception as e:
            print(f"生成总结失败：{e}")
            return self._conversation_summary

    def _save_today_memory(self) -> None:
        """
        保存今天的记忆到文件（累积保存，不是覆盖）
        """
        if not self._current_date_file:
            return

        try:
            from datetime import datetime

            # 先读取现有文件内容（如果存在）
            existing_data = {}
            if self._current_date_file.exists():
                with open(self._current_date_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            # 获取现有的对话历史（如果没有则为空列表）
            existing_history = existing_data.get("conversation_history", [])

            # 将当前内存中的对话添加到历史记录
            current_messages_json = []
            for msg in self._messages:
                msg_dict = {
                    "role": "user" if isinstance(msg, HumanMessage) else "assistant",
                    "content": msg.content,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                current_messages_json.append(msg_dict)

            # 关键改进：只追加不在现有历史中的新对话
            new_messages = []
            for current_msg in current_messages_json:
                is_duplicate = False
                # 检查是否已存在于历史记录中
                for existing_msg in existing_history:
                    # 如果内容和角色都相同，认为是重复的
                    if (current_msg["content"] == existing_msg["content"] and
                            current_msg["role"] == existing_msg["role"]):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    new_messages.append(current_msg)

            # 只有新消息才追加
            if new_messages:
                conversation_history = existing_history + new_messages
                print(f"✨ 新增 {len(new_messages)} 条对话，总计 {len(conversation_history)} 条")
            else:
                conversation_history = existing_history
                print("ℹ️ 没有新的对话需要保存")

            # 构建新的数据结构
            memory_data = {
                "date": self._current_date_str,
                "summary": self._conversation_summary,  # AI 生成的总结
                "conversation_history": conversation_history,  # 完整的对话历史
                "message_count": len(conversation_history),
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # 保存到文件
            with open(self._current_date_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)

            print(f"✅ 已保存今天记忆到：{self._current_date_file.name} (共 {len(conversation_history)} 条对话)")

        except Exception as e:
            print(f"⚠️ 保存今天记忆失败：{e}")

    async def _check_and_generate_periodic_summary(self) -> None:
        """
        检查是否需要生成本周总结（每天都生成，基于本周已过去的天数）
        只要有日期文件，就生成从本周第一天到今天的总结
        """
        files = self._get_date_files()
            
        # 如果没有任何文件，不生成
        if len(files) == 0:
            return
            
        # 获取本周的所有文件（最多 7 个）
        current_week_files = files[:7]
        current_week_dates = [f.stem for f in current_week_files]
            
        print(f"\n🔍 检测周期总结：当前有 {len(current_week_files)} 个文件 - {current_week_dates}")
            
        # 检查是否已经为当前这些天生成过本周总结
        permanent_file = self.date_folder / "permanent_summary.json"
        should_generate = False
            
        if permanent_file.exists():
            try:
                with open(permanent_file, 'r', encoding='utf-8') as f:
                    permanent_data = json.load(f)
                    
                last_summary_dates = permanent_data.get("covered_dates", [])
                print(f"📊 上次总结覆盖：{len(last_summary_dates)} 天 - {last_summary_dates}")
                    
                # 如果当前本周的日期和上次完全一样，说明没有新数据，不需要重新生成
                if set(current_week_dates) == set(last_summary_dates):
                    print(f"ℹ️ 本周总结已覆盖 {len(last_summary_dates)} 天，无需更新")
                    return
                else:
                    # 检查是否有新的天被添加
                    new_days = set(current_week_dates) - set(last_summary_dates)
                    missing_days = set(last_summary_dates) - set(current_week_dates)
                        
                    if new_days:
                        print(f"📝 检测到 {len(new_days)} 个新的对话日期：{sorted(list(new_days))}")
                        should_generate = True
                    elif missing_days:
                        print(f"⚠️ 检测到 {len(missing_days)} 个日期缺失：{sorted(list(missing_days))}")
                        should_generate = True
                    else:
                        print(f"ℹ️ 本周总结已覆盖 {len(last_summary_dates)} 天，无需更新")
                        return
            except Exception as e:
                print(f"⚠️ 检查本周总结失败：{e}")
                import traceback
                traceback.print_exc()
                should_generate = True
        else:
            # 永久总结文件不存在，需要生成
            print("📄 永久总结文件不存在，需要生成")
            should_generate = True
            
        # 生成本周总结（基于已有的所有天数）
        if should_generate:
            print(f"\n🔄 正在为本周 {len(current_week_files)} 天的对话生成总结...")
            await self.generate_periodic_summary(force=True)

    async def generate_periodic_summary(self, force: bool = False) -> str:
        """
        生成 7 天周期的永久总结
        
        Args:
            force: 是否强制生成（即使不足 7 天）
            
        Returns:
            生成的周期总结文本
        """
        if not self.date_folder:
            return ""

        files = self._get_date_files()

        if len(files) < 7 and not force:
            print(f"ℹ️ 当前只有 {len(files)} 个文件，需要 7 个文件才能生成周期总结")
            return self._permanent_summary

        try:
            # 读取最近 7 天的总结
            weekly_summaries = []
            covered_dates = []

            for file in files[:7]:  # 只取最近 7 天
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    date = file.stem
                    summary = data.get("summary", "")
                    if summary:
                        weekly_summaries.append(f"【{date}】{summary}")
                        covered_dates.append(date)
                except Exception as e:
                    print(f"⚠️ 读取文件 {file.name} 失败：{e}")

            if not weekly_summaries:
                print("⚠️ 没有找到有效的每日总结")
                return self._permanent_summary

            # 构建周期总结提示词
            weekly_text = '\n'.join(weekly_summaries)
            prompt = f"""请总结以下 7 天对话中的重要内容，提取关键信息、重要决定、待办事项等：

{weekly_text}

请用结构化的方式总结（300 字以内），包括：
1. 主要讨论的话题
2. 重要的决定或结论
3. 待办事项或后续行动

直接输出总结内容，不要其他说明："""

            # 异步调用 LLM
            response = await self.llm.ainvoke(prompt)
            periodic_summary = response.content.strip()

            # 更新永久总结
            if periodic_summary:
                self._permanent_summary = periodic_summary
                # 保存到永久总结文件
                self._save_permanent_summary(covered_dates)
                print(f"✅ 已生成周期总结：{len(periodic_summary)} 字")

            return periodic_summary

        except Exception as e:
            print(f"生成周期总结失败：{e}")
            return self._permanent_summary

    def load_permanent_summary(self) -> None:
        """
        加载永久总结
        """
        if not self.date_folder:
            return

        permanent_file = self.date_folder / "permanent_summary.json"
        if not permanent_file.exists():
            print("ℹ️ 未找到永久总结文件")
            self._permanent_summary = ""
            return

        try:
            with open(permanent_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._permanent_summary = data.get("summary", "")
            print(f"✅ 已加载永久总结：{len(self._permanent_summary)} 字")

        except Exception as e:
            print(f"⚠️ 加载永久总结失败：{e}")
            self._permanent_summary = ""

    def _save_permanent_summary(self, covered_dates: List[str]) -> None:
        """
        保存永久总结到文件
            
        Args:
            covered_dates: 本次总结覆盖的日期列表
        """
        if not self.date_folder:
            return

        try:
            from datetime import datetime

            permanent_file = self.date_folder / "permanent_summary.json"

            # 如果是首次创建，保留历史记录
            existing_summaries = []
            if permanent_file.exists():
                try:
                    with open(permanent_file, 'r', encoding='utf-8') as f:
                        old_data = json.load(f)
                    existing_summaries = old_data.get("history", [])
                except Exception:
                    pass

            # 添加新的周期总结到历史
            new_entry = {
                "period": f"{covered_dates[-1]} - {covered_dates[0]}",
                "summary": self._permanent_summary,
                "covered_dates": covered_dates,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            existing_summaries.insert(0, new_entry)  # 新的在前

            # 保留最近 10 个周期的历史
            existing_summaries = existing_summaries[:10]

            permanent_data = {
                "summary": self._permanent_summary,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "covered_dates": covered_dates,
                "history": existing_summaries
            }

            with open(permanent_file, 'w', encoding='utf-8') as f:
                json.dump(permanent_data, f, ensure_ascii=False, indent=2)

            print(f"✅ 已保存永久总结到：{permanent_file.name}")

        except Exception as e:
            print(f"⚠️ 保存永久总结失败：{e}")

    def get_memory_status(self) -> Dict:
        """
        获取记忆状态信息
        
        Returns:
            包含记忆状态的字典
        """
        date_files = self._get_date_files()

        return {
            "current_messages": len(self._messages),
            "estimated_tokens": self.estimate_tokens(),
            "today_summary_length": len(self._conversation_summary),
            "permanent_summary_length": len(self._permanent_summary),
            "date_folder": str(self.date_folder) if self.date_folder else None,
            "available_date_files": len(date_files),
            "max_date_files": 7,
            "current_date_file": self._current_date_file.name if self._current_date_file else None,
            "max_tokens": self.max_tokens,
            "max_messages": self.max_messages
        }


# ==================== 工具函数 ====================

def create_memory_manager(max_tokens: int = 4000,
                          max_messages: Optional[int] = None,
                          date_folder: Optional[str] = "Date",
                          enable_summary: bool = True) -> MemoryManager:
    """
    创建记忆管理器实例
    
    Args:
        max_tokens: 最大 token 数限制
        max_messages: 最大消息数量限制
        date_folder: 日期文件夹路径（默认为当前目录下的 Date文件夹）
        enable_summary: 是否启用对话总结
        
    Returns:
        MemoryManager 实例
    """
    # 如果是相对路径，则相对于当前文件所在目录
    if date_folder and not Path(date_folder).is_absolute():
        # 获取当前文件所在目录
        current_dir = Path(__file__).parent
        date_folder = current_dir / date_folder

    return MemoryManager(
        max_tokens=max_tokens,
        max_messages=max_messages,
        date_folder=date_folder,
        enable_summary=enable_summary
    )
