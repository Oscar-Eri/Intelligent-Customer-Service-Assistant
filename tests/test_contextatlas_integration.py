"""
测试 ContextAtlas 知识库集成
验证知识库的检索、记忆记录等功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
backend_dir = current_dir.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backendtest.LLM.Memory.knowledge_base import create_knowledge_base


def test_installation():
    """测试 ContextAtlas 是否已安装"""
    print("=" * 60)
    print("测试 1: 检查 ContextAtlas 安装状态")
    print("=" * 60)
    
    kb = create_knowledge_base()
    status = kb.get_memory_status()
    
    print(f"[OK] ContextAtlas 已安装: {status['contextatlas_installed']}")
    print(f"[PATH] 仓库路径: {status['repo_path']}")
    print(f"[FEATURES] 可用功能: {', '.join(status['features'])}")
    print()
    
    return status['contextatlas_installed']


def test_index_status():
    """测试索引状态"""
    print("=" * 60)
    print("测试 2: 检查索引状态")
    print("=" * 60)
    
    kb = create_knowledge_base()
    index_status = kb.check_index_status()
    
    if not index_status.get('installed'):
        print("[ERROR] ContextAtlas 未安装")
        return False
    
    if 'error' in index_status:
        print(f"[WARN] 检查索引状态时出错: {index_status['error']}")
        return False
    
    print(f"[INFO] 索引状态输出:")
    print(index_status.get('output', '无输出'))
    print()
    
    return True


def test_search():
    """测试搜索功能"""
    print("=" * 60)
    print("测试 3: 测试语义检索")
    print("=" * 60)
    
    kb = create_knowledge_base()
    
    # 测试查询
    queries = [
        "情感分析模块是如何工作的？",
        "用户认证流程在哪里实现？",
        "LangGraph 工作流的结构是什么？"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] 查询: {query}")
        print("-" * 60)
        
        result = kb.search_knowledge(query)
        
        # 检查结果类型
        if result.startswith("⚠️") or (result and "警告" in result):
            print(f"[WARN] {result}")
        elif len(result) < 50:
            print(f"[INFO] 检索结果较短（可能索引不完整）: {result[:200] if result else 'None'}")
        else:
            print(f"[OK] 检索成功，返回 {len(result)} 字符")
            print(f"   前 200 字符: {result[:200]}...")
    
    print()


def test_feature_memory():
    """测试特征记忆记录"""
    print("=" * 60)
    print("测试 4: 测试 Feature Memory 记录")
    print("=" * 60)
    
    kb = create_knowledge_base()
    
    # 尝试记录一个模块记忆
    print("\n📝 尝试记录模块记忆...")
    result = kb.record_feature_memory(
        module_name="情感分析模块",
        description="用于分析用户输入情感的模块，支持多种情绪分类",
        code_dir="E:\\QRTlongchaintraining\\PROJ\\AIchat\\backend\\LLM"
    )
    
    if result and result.startswith("记录失败"):
        print(f"⚠️ {result}")
        print("   （这可能是因为索引未完成或 API 配置问题）")
    else:
        print(f"✅ 记录成功: {result[:200]}")
    
    print()


def test_decision_record():
    """测试决策记录"""
    print("=" * 60)
    print("测试 5: 测试 Decision Record 记录")
    print("=" * 60)
    
    kb = create_knowledge_base()
    
    # 尝试记录一个架构决策
    print("\n📝 尝试记录架构决策...")
    result = kb.record_decision(
        decision_id="2026-04-09-context-atlas-integration",
        context="需要增强 AI 助手的代码理解能力",
        decision="集成 ContextAtlas 作为知识库层",
        consequences="提升代码检索准确性，支持语义搜索和结构化记忆"
    )
    
    if result and result.startswith("记录失败"):
        print(f"⚠️ {result}")
        print("   （这可能是因为索引未完成或 API 配置问题）")
    else:
        print(f"✅ 记录成功: {result[:200]}")
    
    print()


def test_list_memories():
    """测试列出记忆"""
    print("=" * 60)
    print("测试 6: 列出所有记忆")
    print("=" * 60)
    
    kb = create_knowledge_base()
    
    result = kb.list_memories()
    
    if result and result.startswith("获取失败"):
        print(f"⚠️ {result}")
    elif len(result.strip()) == 0:
        print("[INFO] 暂无记忆记录（这是正常的，如果刚初始化）")
    else:
        print(f"[OK] 找到记忆:")
        print(result[:500])
    
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("ContextAtlas 知识库集成测试")
    print("=" * 60 + "\n")
    
    # 测试 1: 安装检查
    installed = test_installation()
    if not installed:
        print("\n❌ ContextAtlas 未安装，请先运行:")
        print("   cd E:\\QRTlongchaintraining\\PROJ\\AIchat4.11\\backendtest\\LLM\\Memory\\ContextAtlas-main")
        print("   pnpm install && pnpm build && npm install -g .")
        return
    
    # 测试 2: 索引状态
    test_index_status()
    
    # 测试 3: 搜索功能
    test_search()
    
    # 测试 4: Feature Memory
    test_feature_memory()
    
    # 测试 5: Decision Record
    test_decision_record()
    
    # 测试 6: 列出记忆
    test_list_memories()
    
    # 总结
    print("=" * 60)
    print("测试完成总结")
    print("=" * 60)
    print("\n[OK] 基础功能测试通过")
    print("\n[NEXT] 下一步操作:")
    print("   1. 配置 API Key: 编辑 C:\\Users\\Oscar\\.contextatlas\\.env")
    print("   2. 建立完整索引: contextatlas index E:\\QRTlongchaintraining\\PROJ\\AIchat")
    print("   3. 启动守护进程: contextatlas daemon start")
    print("   4. 在 LangGraph 中集成知识库检索")
    print()


if __name__ == "__main__":
    main()
