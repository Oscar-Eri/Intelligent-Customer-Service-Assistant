"""
测试 ContextAtlas 知识库集成 - 简化版（避免编码问题）
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
backend_dir = current_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backendtest.LLM.Memory.knowledge_base import create_knowledge_base


def main():
    """运行测试"""
    print("\n" + "=" * 60)
    print("ContextAtlas Knowledge Base Integration Test")
    print("=" * 60 + "\n")
    
    # 创建知识库实例
    kb = create_knowledge_base()
    status = kb.get_memory_status()
    
    print(f"[1] Installation Status:")
    print(f"    Installed: {status['contextatlas_installed']}")
    print(f"    Repo Path: {status['repo_path']}")
    print(f"    Features: {', '.join(status['features'])}\n")
    
    if not status['contextatlas_installed']:
        print("[ERROR] ContextAtlas is not installed!")
        print("Please run:")
        print("  cd E:\\QRTlongchaintraining\\PROJ\\AIchat4.11\\backendtest\\LLM\\Memory\\ContextAtlas-main")
        print("  pnpm install && pnpm build && npm install -g .\n")
        return
    
    # 测试搜索
    print(f"[2] Testing Search Functionality:")
    test_query = "emotional analysis module"
    print(f"    Query: {test_query}")
    
    result = kb.search_knowledge(test_query)
    
    if result:
        if len(result) < 100:
            print(f"    Result (short): {result[:200]}")
        else:
            print(f"    Result length: {len(result)} characters")
            print(f"    Preview: {result[:150]}...")
    else:
        print(f"    Result: None (index may be incomplete)")
    
    print()
    
    # 总结
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("\n[OK] Basic integration successful!")
    print("\n[Next Steps]:")
    print("  1. Configure API Key: Edit C:\\Users\\Oscar\\.contextatlas\\.env")
    print("  2. Build full index: contextatlas index E:\\QRTlongchaintraining\\PROJ\\AIchat")
    print("  3. Start daemon: contextatlas daemon start")
    print("  4. Integrate with LangGraph workflow\n")


if __name__ == "__main__":
    main()
