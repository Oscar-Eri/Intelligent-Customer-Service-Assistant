"""
知识库摘要生成器
使用 LLM 自动生成知识库文件的结构化摘要,形成"知识地图"

功能:
- 扫描知识库目录结构
- 为每个文件生成简洁摘要
- 大文件自动分块并生成块级摘要
- 支持断点续传(缓存机制)
- 并发调用 LLM API 提高效率

使用示例:
    python backendtest/LLM/RAG/generate_summary.py
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Union, Optional
import httpx
import tiktoken


# ==================== 配置参数 ====================

# 摘要长度限制(token数)
MAX_SUMMARY_TOKENS = 10

# 大文件分块阈值
MAX_CHUNK_TOKENS = 3000
MIN_CHUNK_TOKENS = 1000

# Token 显示间隔(用于行号标注)
TOKEN_DISPLAY_INTERVAL = 100


class SummaryGenerator:
    """
    知识库摘要生成器
    
    工作流程:
    1. 扫描知识库所有 .md 文件
    2. 计算每个文件的 token 数
    3. 小文件直接生成摘要
    4. 大文件先分块,再为每个块生成摘要
    5. 构建目录树结构并保存为 summary.txt
    """
    
    def __init__(self, base_path: str = None, chunks_dir: str = None, output_file: str = None):
        """
        初始化摘要生成器
        
        Args:
            base_path: 原始知识库路径
            chunks_dir: 分块后文件存储路径
            output_file: 摘要输出文件路径
        """
        # 默认路径配置
        if base_path is None:
            current_dir = Path(__file__).parent.parent.parent.parent
            base_path = str(current_dir / "Knowledge-Base")
        
        if chunks_dir is None:
            current_dir = Path(__file__).parent.parent.parent.parent
            chunks_dir = str(current_dir / "Knowledge-Base-Chunks")
        
        if output_file is None:
            current_dir = Path(__file__).parent.parent.parent.parent
            output_file = str(current_dir / "Knowledge-Base-File-Summary" / "summary.txt")
        
        self.base_path = Path(base_path)
        self.chunks_dir = Path(chunks_dir)
        self.output_file = Path(output_file)
        self.cache_file = self.output_file.parent / "summary_cache.json"
        
        # 初始化 tokenizer
        self.encoder = tiktoken.get_encoding("cl100k_base")
        
        # LLM 配置(使用通义千问)
        import sys
        from pathlib import Path as SysPath
        current_dir = SysPath(__file__).parent.parent.parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        try:
            from config import qwen_base_url, qwen_api_key
        except ImportError:
            from backendtest.config import qwen_base_url, qwen_api_key
        
        self.api_url = f"{qwen_base_url}/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {qwen_api_key}"
        }
        self.model = "qwen-plus"
        
        # 加载缓存
        self.cache = self._load_cache()
        
        print(f"📝 摘要生成器初始化完成")
        print(f"   知识库路径: {self.base_path}")
        print(f"   分块目录: {self.chunks_dir}")
        print(f"   输出文件: {self.output_file}")
    
    async def _generate_file_summary(self, file_path: Path, relative_path: str, max_retries: int = 5) -> Union[str, List[Dict]]:
        """
        为单个文件生成摘要
        
        - 小文件(< 3000 tokens): 返回字符串摘要
        - 大文件(>= 3000 tokens): 返回分块摘要列表 [{"start": 1, "end": 63, "summary": "..."}]
        
        Args:
            file_path: 文件路径
            relative_path: 相对路径(用于缓存键)
            max_retries: 最大重试次数
            
        Returns:
            摘要字符串或分块摘要列表
        """
        # 检查缓存
        if relative_path in self.cache:
            print(f"✅ 使用缓存摘要: {relative_path}")
            return self.cache[relative_path]
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            total_tokens = self._count_tokens(content)
            
            # 判断是否需要分块
            if total_tokens > MAX_CHUNK_TOKENS:
                # 大文件: 分块处理
                return await self._process_large_file(file_path, relative_path, content, total_tokens, max_retries)
            else:
                # 小文件: 直接生成摘要
                return await self._process_small_file(file_path, relative_path, content, total_tokens, max_retries)
        
        except Exception as e:
            print(f"❌ 处理文件失败 {relative_path}: {e}")
            return None
    
    async def _process_small_file(self, file_path: Path, relative_path: str, content: str, total_tokens: int, max_retries: int) -> str:
        """处理小文件,生成单一摘要"""
        prompt = f"""- 任务: 为文件生成内容摘要
- 目标: 让 LLM 了解文件大致内容,以便在众多文件中决定是否读取该文件
- 长度: 摘要 token 数 < {MAX_SUMMARY_TOKENS}
- 文件路径: {relative_path}
- 要求: 
  * 禁止包含文件路径中的词汇
  * 禁止低信息密度词汇(如"的"、"它"、"这个"、"概述"、"文档")
  * 尽量将关键信息直接放入摘要

> 以下是文件内容

{content}

""".strip()
        
        messages = [{"role": "user", "content": prompt}]
        
        # 调用 LLM
        result = await self._call_llm(messages, max_retries)
        
        if result:
            # 清理换行和多余空格
            summary = result.replace('\n', ' ').replace('\r', ' ')
            summary = ' '.join(summary.split())
            
            # 复制小文件到分块目录
            self._copy_small_file(file_path, relative_path)
            
            # 保存到缓存
            self.cache[relative_path] = summary
            self._save_cache()
            
            print(f"✅ 生成摘要 ({total_tokens} tokens): {relative_path}")
            return summary
        
        return None
    
    async def _process_large_file(self, file_path: Path, relative_path: str, content: str, total_tokens: int, max_retries: int) -> List[Dict]:
        """处理大文件,分块并生成块级摘要"""
        lines = content.split('\n')
        num_chunks = (total_tokens // MAX_CHUNK_TOKENS) + 1
        
        # 构建带行号和 token 计数的内容
        lines_with_info = []
        cumulative_tokens = 0
        next_mark = 0
        
        for i, line in enumerate(lines, 1):
            show_count = cumulative_tokens >= next_mark
            prefix = f"{i}({cumulative_tokens})" if show_count else str(i)
            lines_with_info.append(f"{prefix} {line}")
            
            if show_count:
                next_mark = ((cumulative_tokens // TOKEN_DISPLAY_INTERVAL) + 1) * TOKEN_DISPLAY_INTERVAL
            
            cumulative_tokens += self._count_tokens(line)
        
        content_with_lines = '\n'.join(lines_with_info)
        
        prompt = f"""- 任务: 将以下大文件拆分为 {num_chunks} 个小文件,并为每个小文件提供内容摘要
- 目标: 让 LLM 了解文件大致内容,以便在众多文件中决定是否读取该文件
- 长度: {MIN_CHUNK_TOKENS} < 小文件 token 数 < {MAX_CHUNK_TOKENS}, 摘要 token 数 < {MAX_SUMMARY_TOKENS}
- 大文件: {relative_path}
- 输出格式: 单行 JSON,不含代码块,格式如 [{{"start": 起始行号, "end": 结束行号, "summary": "内容摘要"}}]
- 要求:
  * 禁止包含文件路径中的词汇
  * 禁止低信息密度词汇
  * 不要粗暴截断语义完整的段落和句子!!!
  * 尽量将关键信息直接放入摘要!!!

> 以下是大文件内容,每行左侧数字为行号,括号内为累计 token 数

{content_with_lines}

""".strip()
        
        messages = [{"role": "user", "content": prompt}]
        
        # 调用 LLM
        result = await self._call_llm(messages, max_retries)
        
        if result:
            try:
                # 移除可能的代码块标记
                if result.startswith("```"):
                    result = result.split("\n", 1)[1]
                if result.endswith("```"):
                    result = result.rsplit("\n", 1)[0]
                
                chunks = json.loads(result)
                
                # 保存分块文件
                self._save_chunk_files(file_path, relative_path, chunks, lines)
                
                # 保存到缓存
                self.cache[relative_path] = chunks
                self._save_cache()
                
                print(f"✅ 拆分并摘要 ({total_tokens} tokens -> {len(chunks)} 块): {relative_path}")
                return chunks
            
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON 解析失败 {relative_path}: {e}")
                return None
        
        return None
    
    async def _call_llm(self, messages: List[Dict], max_retries: int) -> Optional[str]:
        """
        调用 LLM API,支持指数退避重试
        
        Args:
            messages: 消息列表
            max_retries: 最大重试次数
            
        Returns:
            LLM 响应文本
        """
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    payload = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0,
                        "stream": False,
                        "max_tokens": 4000
                    }
                    
                    response = await client.post(self.api_url, json=payload, headers=self.headers)
                    response.raise_for_status()
                    
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        return data["choices"][0]["message"].get("content", "").strip()
            
            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                wait_time = (2 ** attempt) * 0.5
                print(f"⚠️  第 {attempt + 1}/{max_retries} 次尝试失败: {e}")
                
                if attempt < max_retries - 1:
                    print(f"   {wait_time}s 后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ 达到最大重试次数")
                    return None
        
        return None
    
    def _count_tokens(self, text: str) -> int:
        """计算文本的 token 数"""
        return len(self.encoder.encode(text))
    
    def _save_chunk_files(self, file_path: Path, relative_path: str, chunks: List[Dict], lines: List[str]):
        """保存分块文件到 Knowledge-Base-Chunks 目录"""
        file_stem = file_path.stem
        parent_path = file_path.parent.relative_to(self.base_path)
        chunk_base_dir = self.chunks_dir / parent_path / file_stem
        chunk_base_dir.mkdir(parents=True, exist_ok=True)
        
        for chunk in chunks:
            start = chunk["start"]
            end = chunk["end"]
            
            # 提取对应行的内容
            chunk_lines = lines[start-1:end]
            chunk_content = '\n'.join(chunk_lines)
            
            # 保存为 1-63.md 格式
            chunk_file = chunk_base_dir / f"{start}-{end}.md"
            with open(chunk_file, 'w', encoding='utf-8') as f:
                f.write(chunk_content)
    
    def _copy_small_file(self, file_path: Path, relative_path: str):
        """复制小文件到 Knowledge-Base-Chunks 目录"""
        parent_path = file_path.parent.relative_to(self.base_path)
        target_dir = self.chunks_dir / parent_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        target_file = target_dir / file_path.name
        
        with open(file_path, 'r', encoding='utf-8') as src:
            content = src.read()
        with open(target_file, 'w', encoding='utf-8') as dst:
            dst.write(content)
    
    def _collect_all_files(self) -> List[tuple]:
        """收集所有需要处理的 .md 文件"""
        files = []
        for md_file in self.base_path.rglob("*.md"):
            relative_path = str(md_file.relative_to(self.base_path))
            files.append((md_file, relative_path))
        return files
    
    async def _process_files_with_delay(self, files: List[tuple]) -> Dict[str, Union[str, List[Dict]]]:
        """
        并发处理文件,每次请求间隔 0.5 秒
        
        Args:
            files: [(file_path, relative_path), ...]
            
        Returns:
            {relative_path: summary_or_chunks}
        """
        summaries = {}
        tasks = []
        
        for i, (file_path, relative_path) in enumerate(files):
            async def delayed_task(fp, rp, delay):
                await asyncio.sleep(delay)
                return rp, await self._generate_file_summary(fp, rp)
            
            task = delayed_task(file_path, relative_path, i * 0.5)
            tasks.append(task)
        
        # 并发执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                print(f"❌ 任务失败: {result}")
            elif result:
                rel_path, summary = result
                if summary:
                    summaries[rel_path] = summary
        
        return summaries
    
    def _scan_directory(self, path: Path, prefix: str = "", summaries: Dict = None) -> List[str]:
        """
        递归扫描目录,生成带摘要的树结构
        
        Args:
            path: 当前目录路径
            prefix: 前缀字符串(用于缩进)
            summaries: {relative_path: summary_or_chunks}
            
        Returns:
            树结构的行列表
        """
        lines = []
        if not path.exists():
            return lines
        
        items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        
        for i, item in enumerate(items):
            if item.name.startswith('.'):
                continue
            
            is_last_item = (i == len(items) - 1)
            connector = "└──" if is_last_item else "├──"
            
            if item.is_dir():
                # 目录
                lines.append(f"{prefix}{connector} {item.name}")
                
                extension = "   " if is_last_item else "│  "
                sub_lines = self._scan_directory(item, prefix + extension, summaries)
                lines.extend(sub_lines)
                
                if not is_last_item and sub_lines:
                    lines.append(f"{prefix}│")
            else:
                # 文件
                file_relative = str(item.relative_to(self.base_path))
                file_summary = summaries.get(file_relative, "")
                
                if isinstance(file_summary, list):
                    # 分块文件
                    chunks = file_summary
                    file_name_no_ext = item.stem
                    lines.append(f"{prefix}{connector} {file_name_no_ext}")
                    
                    chunk_extension = "   " if is_last_item else "│  "
                    for chunk_idx, chunk in enumerate(chunks):
                        is_last_chunk = (chunk_idx == len(chunks) - 1)
                        chunk_connector = "└──" if is_last_chunk else "├──"
                        
                        start = chunk.get("start", "?")
                        end = chunk.get("end", "?")
                        summary = chunk.get("summary", "")
                        
                        lines.append(f"{prefix}{chunk_extension}{chunk_connector} {start}-{end}.md：{summary}")
                
                elif file_summary:
                    # 普通文件
                    lines.append(f"{prefix}{connector} {item.name}：{file_summary}")
                else:
                    lines.append(f"{prefix}{connector} {item.name}")
        
        return lines
    
    def _load_cache(self) -> Dict:
        """加载缓存的摘要"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  加载缓存失败: {e}")
        return {}
    
    def _save_cache(self):
        """保存缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存缓存失败: {e}")
    
    async def generate(self):
        """生成完整的知识库摘要"""
        print("=" * 60)
        print("知识库摘要生成器")
        print("=" * 60)
        print(f"📁 知识库路径: {self.base_path}")
        print(f"📄 输出文件: {self.output_file}")
        print(f"🤖 模型: {self.model}")
        print("=" * 60)
        
        # 1. 收集所有文件
        print("\n📂 收集文件...")
        files = self._collect_all_files()
        
        # 计算总 token 数
        total_kb_tokens = 0
        for file_path, _ in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    total_kb_tokens += self._count_tokens(content)
            except Exception as e:
                print(f"⚠️  读取失败 {file_path}: {e}")
        
        print(f"🔍 找到 {len(files)} 个文件")
        print(f"📊 知识库总 token 数: {total_kb_tokens:,}")
        
        # 2. 生成文件摘要
        print("\n🔄 生成文件摘要(并发,间隔 0.5s)...")
        start_time = time.time()
        file_summaries = await self._process_files_with_delay(files)
        elapsed = time.time() - start_time
        print(f"🎉 生成 {len(file_summaries)}/{len(files)} 个摘要,耗时 {elapsed:.1f}s")
        
        # 3. 构建树结构
        print("\n🌲 构建树结构...")
        lines = ["."]
        lines.extend(self._scan_directory(self.base_path, summaries=file_summaries))
        
        # 4. 写入文件
        print(f"\n💾 写入 {self.output_file}...")
        output_content = "\n".join(lines)
        
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(output_content)
        
        # 计算压缩率
        output_tokens = self._count_tokens(output_content)
        compression_ratio = (output_tokens / total_kb_tokens * 100) if total_kb_tokens > 0 else 0
        
        print("=" * 60)
        print("😊 摘要生成完成!")
        print(f"📊 总文件数: {len(files)}")
        print(f"📊 成功摘要: {len(file_summaries)}")
        print(f"📄 输出文件: {self.output_file}")
        print(f"📊 输出 token 数: {output_tokens:,}")
        print(f"📊 压缩率: {compression_ratio:.2f}%")
        print("=" * 60)


async def main():
    """主函数"""
    generator = SummaryGenerator()
    await generator.generate()


if __name__ == "__main__":
    asyncio.run(main())
