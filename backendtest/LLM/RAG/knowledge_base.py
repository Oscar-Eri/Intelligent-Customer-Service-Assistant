"""
知识库管理模块
负责知识库文件的检索和管理,支持文件和目录级别的检索
高内聚低耦合设计,独立于其他模块
"""
import aiofiles
from pathlib import Path
from typing import List, Dict, Optional


class KnowledgeBaseManager:
    """
    知识库管理器
    
    功能:
    - 检索指定文件或目录的内容
    - 获取知识库文件摘要(知识地图)
    - 列出知识库文件树结构
    
    使用示例:
        kb = KnowledgeBaseManager(base_path="./Knowledge-Base")
        content = await kb.retrieve_files(["Product-Line-A/SW-2100.md"])
    """
    
    def __init__(self, base_path: str = None, summary_file: str = None):
        """
        初始化知识库管理器
        
        Args:
            base_path: 知识库基础路径(分块后的文件目录)
            summary_file: 知识库摘要文件路径(知识地图)
        """
        # 默认使用项目根目录下的 Knowledge-Base-Chunks
        if base_path is None:
            current_dir = Path(__file__).parent.parent.parent.parent  # 上四级到 AIchat4.11
            base_path = str(current_dir / "Knowledge-Base-Chunks")
        
        self.base_path = Path(base_path)
        
        # 默认使用项目根目录下的 summary.txt
        if summary_file is None:
            current_dir = Path(__file__).parent.parent.parent.parent  # 上四级到 AIchat4.11
            summary_file = str(current_dir / "Knowledge-Base-File-Summary" / "summary.txt")
        
        self.summary_file = Path(summary_file)
        
        print(f"📚 知识库管理器初始化完成")
        print(f"   基础路径: {self.base_path}")
        print(f"   摘要文件: {self.summary_file}")
    
    async def get_file_summary(self) -> str:
        """
        获取知识库文件摘要(知识地图)
        
        摘要文件由 generate_summary.py 脚本生成,包含:
        - 知识库目录树结构
        - 每个文件的简要内容摘要
        - 大文件的分块信息
        
        Returns:
            知识库摘要文本,如果文件不存在则返回提示信息
        """
        if self.summary_file.exists():
            async with aiofiles.open(self.summary_file, 'r', encoding='utf-8') as f:
                return await f.read()
        
        return (
            "⚠️ 知识库摘要文件未找到。\n\n"
            "请先运行以下命令生成摘要:\n"
            "python backendtest/LLM/RAG/generate_summary.py\n\n"
            f"期望的文件路径: {self.summary_file}"
        )
    
    async def retrieve_files(self, file_paths: List[str]) -> str:
        """
        检索指定文件或目录的内容
        
        支持三种检索模式:
        1. 检索单个文件: ["Product-Line-A/SW-2100.md"]
        2. 检索整个目录: ["Product-Line-A/"] (会递归获取所有 .md 文件)
        3. 检索所有文件: ["/"]
        
        Args:
            file_paths: 文件路径或目录路径列表
            
        Returns:
            检索到的文件内容,多个文件用分隔符连接
            
        Example:
            >>> kb = KnowledgeBaseManager()
            >>> content = await kb.retrieve_files(["Product-Line-A/"])
            >>> print(content[:500])  # 查看前500字符
        """
        results = []
        
        for file_path in file_paths:
            full_path = self.base_path / file_path.lstrip('/')
            
            # 情况1: 检索整个目录
            if full_path.is_dir():
                print(f"[DEBUG] 检索目录: {file_path}")
                md_files = list(full_path.rglob("*.md"))
                print(f"[DEBUG] 找到 {len(md_files)} 个文件")
                
                for md_file in sorted(md_files):
                    content = await self._read_file(md_file)
                    relative_path = md_file.relative_to(self.base_path)
                    # 使用书名号标注文件来源
                    results.append(f"《{relative_path}》\n\n{content}")
                    print(f"[DEBUG] 已添加文件: {relative_path}, 长度: {len(content)}")
            
            # 情况2: 检索单个文件
            elif full_path.is_file():
                print(f"[DEBUG] 检索文件: {file_path}")
                content = await self._read_file(full_path)
                results.append(f"《{file_path}》\n\n{content}")
                print(f"[DEBUG] 文件长度: {len(content)}")
            
            # 情况3: 检索所有文件
            elif file_path == "/":
                print(f"[DEBUG] 检索所有文件")
                for md_file in sorted(self.base_path.rglob("*.md")):
                    content = await self._read_file(md_file)
                    relative_path = md_file.relative_to(self.base_path)
                    results.append(f"《{relative_path}》\n\n{content}")
        
        # 用分隔符连接多个文件内容
        final_content = "\n\n==========\n\n".join(results)
        print(f"[DEBUG] 总内容长度: {len(final_content)}, 文件数: {len(results)}")
        
        return final_content
    
    async def _read_file(self, file_path: Path) -> str:
        """
        异步读取文件内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件内容字符串,如果读取失败则返回错误信息
        """
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except Exception as e:
            return f"读取文件错误: {str(e)}"
    
    def list_files(self) -> Dict:
        """
        列出知识库文件树结构
        
        Returns:
            嵌套字典表示的目录树结构
            {
                "type": "directory",
                "name": "根目录名",
                "children": [
                    {"type": "file", "name": "文件名.md", "path": "相对路径"},
                    {"type": "directory", "name": "子目录", "children": [...]}
                ]
            }
            
        Example:
            >>> kb = KnowledgeBaseManager()
            >>> tree = kb.list_files()
            >>> print(json.dumps(tree, indent=2, ensure_ascii=False))
        """
        def scan_dir(path: Path) -> Dict:
            """递归扫描目录"""
            result = {"type": "directory", "name": path.name, "children": []}
            
            if not path.exists():
                return result
            
            # 排序: 目录在前,文件在后,按名称排序
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for item in items:
                # 跳过隐藏文件
                if item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    # 递归扫描子目录
                    result["children"].append(scan_dir(item))
                else:
                    # 添加文件信息
                    result["children"].append({
                        "type": "file",
                        "name": item.name,
                        "path": str(item.relative_to(self.base_path))
                    })
            
            return result
        
        return scan_dir(self.base_path)


# 创建全局单例实例
knowledge_base_manager = KnowledgeBaseManager()
