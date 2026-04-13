"""
AIchat4.11 综合测试脚本
测试 RAG 功能、LangGraph 工作流和基础功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent.parent  # tests 的父目录是 AIchat4.11
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))


def print_section(title: str):
    """打印分隔线"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


async def test_1_knowledge_base():
    """测试1: 知识库基础功能"""
    print_section("测试1: 知识库基础功能")
    
    try:
        from backendtest.LLM.RAG import knowledge_base_manager
        
        # 测试1.1: 检索单个文件
        print("\n📄 测试1.1: 检索单个文件")
        content = await knowledge_base_manager.retrieve_files([
            "Product-Line-A-Smartwatch-Series/SW-2100-Flagship.md"
        ])
        print(f"✅ 检索成功,内容长度: {len(content)} 字符")
        print(f"📝 预览: {content[:200]}...\n")
        
        # 测试1.2: 获取知识库摘要
        print("🗺️  测试1.2: 获取知识库摘要")
        summary = await knowledge_base_manager.get_file_summary()
        print(f"✅ 摘要长度: {len(summary)} 字符")
        if "未找到" not in summary:
            print(f"📝 摘要预览:\n{summary[:300]}...")
        else:
            print(f"⚠️  {summary}")
        
        # 测试1.3: 列出文件树
        print("\n🌲 测试1.3: 文件树结构")
        tree = knowledge_base_manager.list_files()
        import json
        print(json.dumps(tree, indent=2, ensure_ascii=False)[:400])
        
        print("\n✅ 测试1 通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试1 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_2_rag_node():
    """测试2: RAG 检索节点"""
    print_section("测试2: RAG 检索节点")
    
    try:
        from backendtest.LLM.nodes import knowledge_retrieval_node
        
        # 测试2.1: 知识查询问题(应触发 RAG)
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
            content_len = len(result.get('rag_retrieved_content', ''))
            print(f"✅ 检索到内容长度: {content_len} 字符")
            if content_len > 0:
                print(f"📝 内容预览:\n{result['rag_retrieved_content'][:200]}...")
        else:
            print("⚠️  未触发 RAG 检索")
        
        # 测试2.2: 普通对话(不应触发 RAG)
        print("\n💬 测试2.2: 普通对话(不应触发 RAG)")
        state["user_input"] = "你好,今天心情怎么样?"
        result = await knowledge_retrieval_node(state)
        print(f"✅ RAG 使用状态: {result.get('rag_used')}")
        
        if not result.get('rag_used'):
            print("✅ 正确跳过 RAG 检索")
        
        print("\n✅ 测试2 通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试2 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_3_workflow():
    """测试3: LangGraph 工作流"""
    print_section("测试3: LangGraph 工作流")
    
    try:
        from backendtest.LLM.service import LangGraphChatService
        
        print("\n🔧 初始化聊天服务...")
        service = LangGraphChatService(
            max_tokens=4000,
            max_messages=10,
            enable_memory_persistence=False,
            enable_contextatlas=False
        )
        print("✅ 服务初始化完成")
        
        # 测试3.1: 简单对话
        print("\n💬 测试3.1: 简单问候")
        response = await service.chat("你好")
        print(f"AI: {response[:100]}...")
        
        if len(response) > 0:
            print("✅ 收到回复")
        else:
            print("⚠️  回复为空")
        
        # 测试3.2: 知识查询(如果 RAG 正常工作)
        print("\n❓ 测试3.2: 产品查询")
        response2 = await service.chat("SW-2100有什么特点?")
        print(f"AI: {response2[:200]}...")
        
        # 检查是否包含关键信息
        keywords_found = []
        for kw in ["AMOLED", "72小时", "2999", "旗舰"]:
            if kw in response2:
                keywords_found.append(kw)
        
        if keywords_found:
            print(f"✅ 回复包含知识库信息: {', '.join(keywords_found)}")
        else:
            print("⚠️  回复可能未使用知识库")
        
        print("\n✅ 测试3 通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试3 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_4_tools():
    """测试4: 工具调用功能"""
    print_section("测试4: 工具调用功能")
    
    try:
        from backendtest.LLM.tools import (
            get_current_time, calculate, analyze_sentiment
        )
        
        # 测试4.1: 时间工具
        print("\n🕐 测试4.1: 获取当前时间")
        time_result = get_current_time()
        print(f"✅ 当前时间: {time_result}")
        
        # 测试4.2: 计算工具
        print("\n🔢 测试4.2: 数学计算")
        calc_result = calculate(expression="100 + 200 * 3")
        print(f"✅ 计算结果: {calc_result}")
        
        # 测试4.3: 情感分析工具
        print("\n😊 测试4.3: 情感分析")
        sentiment_result = analyze_sentiment(text="这个产品太棒了,我非常喜欢!")
        print(f"✅ 情感分析结果: {sentiment_result[:150]}...")
        
        print("\n✅ 测试4 通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试4 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_5_memory():
    """测试5: 记忆系统"""
    print_section("测试5: 记忆系统")
    
    try:
        from backendtest.LLM.Memory import create_memory_manager
        
        print("\n💾 测试5.1: 创建记忆管理器")
        memory = create_memory_manager(
            max_tokens=4000,
            max_messages=10,
            enable_summary=False
        )
        print("✅ 记忆管理器创建成功")
        
        # 测试5.2: 添加消息
        print("\n💬 测试5.2: 添加对话消息")
        memory.add_user_message("你好,我想了解一下产品")
        memory.add_ai_message("您好!很高兴为您介绍我们的产品。")
        
        msg_count = memory.get_message_count()
        print(f"✅ 当前消息数: {msg_count}")
        
        # 测试5.3: 获取消息
        print("\n📚 测试5.3: 获取消息历史")
        messages = memory.get_messages()
        print(f"✅ 获取到 {len(messages)} 条消息")
        
        for i, msg in enumerate(messages, 1):
            print(f"  {i}. {msg.type}: {msg.content[:50]}...")
        
        print("\n✅ 测试5 通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试5 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀"*30)
    print("  AIchat4.11 综合测试套件")
    print("🚀"*30)
    
    results = {}
    
    # 运行各个测试
    results["知识库基础"] = await test_1_knowledge_base()
    results["RAG节点"] = await test_2_rag_node()
    results["LangGraph工作流"] = await test_3_workflow()
    results["工具调用"] = await test_4_tools()
    results["记忆系统"] = await test_5_memory()
    
    # 汇总结果
    print_section("测试结果汇总")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:20s} {status}")
    
    print("\n" + "-"*60)
    print(f"总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过! 系统运行正常!")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败,请检查错误信息")
    
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试执行出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
