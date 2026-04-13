"""
RAG 功能集成测试
验证知识库检索功能是否正常工作
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))


async def test_knowledge_base_retrieval():
    """测试1: 知识库文件检索功能"""
    print("\n" + "="*60)
    print("测试1: 知识库文件检索")
    print("="*60)
    
    from backendtest.LLM.RAG import knowledge_base_manager
    
    # 测试1.1: 检索单个文件
    print("\n📄 测试1.1: 检索单个文件")
    content = await knowledge_base_manager.retrieve_files([
        "Product-Line-A-Smartwatch-Series/SW-2100-Flagship.md"
    ])
    print(f"✅ 检索成功,内容长度: {len(content)} 字符")
    print(f"📝 内容预览:\n{content[:300]}...\n")
    
    # 测试1.2: 检索整个目录
    print("📁 测试1.2: 检索整个目录")
    content = await knowledge_base_manager.retrieve_files([
        "Product-Line-A-Smartwatch-Series/"
    ])
    print(f"✅ 检索成功,内容长度: {len(content)} 字符")
    
    # 测试1.3: 获取知识库摘要
    print("\n🗺️  测试1.3: 获取知识库摘要")
    summary = await knowledge_base_manager.get_file_summary()
    print(f"✅ 摘要长度: {len(summary)} 字符")
    if "未找到" not in summary:
        print(f"📝 摘要预览:\n{summary[:500]}...")
    else:
        print(f"⚠️  {summary}")
    
    # 测试1.4: 列出文件树
    print("\n🌲 测试1.4: 列出文件树结构")
    tree = knowledge_base_manager.list_files()
    import json
    print(json.dumps(tree, indent=2, ensure_ascii=False)[:500])


async def test_rag_node():
    """测试2: RAG 节点功能"""
    print("\n" + "="*60)
    print("测试2: RAG 检索节点")
    print("="*60)
    
    from backendtest.LLM.nodes import knowledge_retrieval_node
    
    # 测试2.1: 知识查询问题
    print("\n❓ 测试2.1: 知识查询问题")
    state = {
        "user_input": "SW-2100智能手表的电池续航是多少?",
        "messages": [],
        "ai_response": "",
        "needs_human_review": False,
        "sentiment_result": {},
        "intent_result": {},
        "keywords_result": {},
        "entities_result": {},
        "rag_retrieved_content": "",
        "rag_used": False
    }
    
    result = await knowledge_retrieval_node(state)
    print(f"✅ RAG 使用状态: {result.get('rag_used')}")
    if result.get('rag_used'):
        print(f"✅ 检索到内容长度: {len(result.get('rag_retrieved_content', ''))} 字符")
        print(f"📝 内容预览:\n{result['rag_retrieved_content'][:300]}...")
    else:
        print("⚠️  未触发 RAG 检索")
    
    # 测试2.2: 普通对话(不应触发 RAG)
    print("\n💬 测试2.2: 普通对话(不应触发 RAG)")
    state["user_input"] = "你好,今天天气怎么样?"
    result = await knowledge_retrieval_node(state)
    print(f"✅ RAG 使用状态: {result.get('rag_used')}")
    if not result.get('rag_used'):
        print("✅ 正确跳过 RAG 检索")


async def test_full_workflow():
    """测试3: 完整工作流(包含 RAG)"""
    print("\n" + "="*60)
    print("测试3: 完整工作流测试")
    print("="*60)
    
    from backendtest.LLM.service import LangGraphChatService
    
    # 创建服务实例
    print("\n🔧 初始化聊天服务...")
    service = LangGraphChatService(
        max_tokens=4000,
        max_messages=10,
        enable_memory_persistence=False,  # 测试时不持久化
        enable_contextatlas=False
    )
    print("✅ 服务初始化完成")
    
    # 测试3.1: 知识查询
    print("\n❓ 测试3.1: 询问产品规格")
    question = "SW-2100智能手表有哪些主要特性?价格是多少?"
    print(f"用户: {question}")
    
    response = await service.chat(question)
    print(f"AI: {response[:500]}...")
    
    # 检查回复中是否包含关键信息
    if "2999" in response or "AMOLED" in response or "72小时" in response:
        print("✅ 回复包含知识库中的关键信息")
    else:
        print("⚠️  回复可能未正确使用知识库")
    
    # 测试3.2: 市场数据查询
    print("\n📊 测试3.2: 询问市场数据")
    question2 = "2024年华东地区的市场份额是多少?"
    print(f"用户: {question2}")
    
    response2 = await service.chat(question2)
    print(f"AI: {response2[:500]}...")
    
    if "18%" in response2 or "华东" in response2:
        print("✅ 回复包含市场数据")
    else:
        print("⚠️  回复可能未正确使用知识库")


async def main():
    """运行所有测试"""
    print("\n" + "🚀"*30)
    print("开始 RAG 功能集成测试")
    print("🚀"*30)
    
    try:
        # 运行测试
        await test_knowledge_base_retrieval()
        await test_rag_node()
        await test_full_workflow()
        
        print("\n" + "✅"*30)
        print("所有测试完成!")
        print("✅"*30)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
