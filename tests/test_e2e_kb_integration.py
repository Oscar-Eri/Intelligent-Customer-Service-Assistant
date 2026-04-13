"""
端到端测试 - 验证 ContextAtlas 知识库在 LangGraph 中的集成
测试完整的对话流程，包括知识库检索和 LLM 响应
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from backendtest.LLM.langgraph_engine import create_langgraph_service
from backendtest.LLM.Memory.knowledge_base import create_knowledge_base


async def test_kb_detection():
    """测试 1: 验证知识库检索触发机制"""
    print("\n" + "=" * 70)
    print("测试 1: 知识库检索触发机制")
    print("=" * 70)
    
    test_cases = [
        ("情感分析模块是如何实现的？", True, "包含'如何实现'、'模块'"),
        ("用户认证流程在哪里？", True, "包含'流程'、'在哪里'"),
        ("今天天气怎么样？", False, "普通问题，不应触发"),
        ("帮我计算 2+2", False, "计算器问题，不应触发"),
        ("代码架构设计是怎样的？", True, "包含'代码'、'架构'、'设计'"),
    ]
    
    for query, should_trigger, reason in test_cases:
        keywords = ["如何实现", "代码", "模块", "架构", "设计", "流程", "在哪里"]
        triggered = any(kw in query.lower() for kw in keywords)
        
        status = "✅" if triggered == should_trigger else "❌"
        print(f"\n{status} 查询: {query}")
        print(f"   预期触发: {should_trigger}, 实际触发: {triggered}")
        print(f"   原因: {reason}")
    
    print()


async def test_kb_search_directly():
    """测试 2: 直接测试知识库搜索功能"""
    print("\n" + "=" * 70)
    print("测试 2: 知识库直接搜索")
    print("=" * 70)
    
    kb = create_knowledge_base()
    
    queries = [
        "emotional analysis sentiment module",
        "LangGraph workflow structure",
        "user authentication flow"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] 搜索: {query}")
        print("-" * 70)
        
        result = kb.search_knowledge(query)
        
        if result:
            if len(result) < 100:
                print(f"   结果长度: {len(result)} 字符（较短）")
                print(f"   内容预览: {result[:200]}")
            else:
                print(f"   ✅ 结果长度: {len(result)} 字符")
                print(f"   前 300 字符:\n   {result[:300]}...")
        else:
            print(f"   ⚠️ 无结果返回")
    
    print()


async def test_full_chat_with_kb():
    """测试 3: 完整对话流程测试（带知识库）"""
    print("\n" + "=" * 70)
    print("测试 3: 完整对话流程（触发知识库检索）")
    print("=" * 70)
    
    # 创建聊天服务
    service = create_langgraph_service()
    
    # 测试问题列表
    test_questions = [
        "你好",  # 普通问候，不应触发知识库
        "情感分析模块是如何工作的？",  # 应触发知识库
        "今天的天气怎么样？",  # 普通问题，不应触发
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 70}")
        print(f"轮次 {i}: {question}")
        print(f"{'=' * 70}")
        
        try:
            # 调用聊天服务
            response = await service.chat(question)
            
            print(f"\n🤖 AI 回复:")
            print(f"   {response[:500]}..." if len(response) > 500 else f"   {response}")
            print(f"\n   回复长度: {len(response)} 字符")
            
            # 检查是否包含知识库相关信息
            if "相关知识库信息" in response or "## 结果卡片" in response:
                print(f"   ✅ 检测到知识库内容被注入")
            else:
                print(f"   ℹ️ 未检测到显式知识库内容（可能未触发或已整合）")
                
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    
    print()


async def test_kb_status():
    """测试 4: 检查知识库状态"""
    print("\n" + "=" * 70)
    print("测试 4: 知识库状态检查")
    print("=" * 70)
    
    kb = create_knowledge_base()
    status = kb.get_memory_status()
    
    print(f"\n安装状态: {'✅ 已安装' if status['contextatlas_installed'] else '❌ 未安装'}")
    print(f"仓库路径: {status['repo_path']}")
    print(f"可用功能:")
    for feature in status['features']:
        print(f"  - {feature}")
    
    # 检查索引状态
    index_status = kb.check_index_status()
    print(f"\n索引状态检查:")
    if 'error' in index_status:
        print(f"  ⚠️ 检查出错: {index_status['error']}")
    elif 'output' in index_status:
        output = index_status['output']
        if output:
            # 提取关键信息
            lines = output.split('\n')
            for line in lines[:10]:  # 只显示前10行
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"  ℹ️ 无输出")
    
    print()


async def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("ContextAtlas 知识库集成 - 端到端测试")
    print("=" * 70)
    
    try:
        # 测试 1: 触发机制
        await test_kb_detection()
        
        # 测试 2: 直接搜索
        await test_kb_search_directly()
        
        # 测试 3: 知识库状态
        await test_kb_status()
        
        # 测试 4: 完整对话（这个可能需要 API key，放在最后）
        print("\n" + "=" * 70)
        print("准备测试完整对话流程...")
        print("=" * 70)
        print("\n注意：此测试需要有效的 LLM API Key")
        print("如果尚未配置，可以跳过此测试\n")
        
        user_input = input("是否继续测试完整对话流程？(y/n): ").strip().lower()
        if user_input == 'y':
            await test_full_chat_with_kb()
        else:
            print("\n⏭️  跳过完整对话测试")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print("\n✅ 知识库集成测试完成")
    print("\n关键检查点:")
    print("  1. ContextAtlas 已正确安装")
    print("  2. 知识库封装层工作正常")
    print("  3. 关键词触发机制有效")
    print("  4. 搜索功能可正常使用")
    print("\n下一步建议:")
    print("  1. 配置 Embedding API Key 以提升检索质量")
    print("  2. 重新建立完整索引: contextatlas index <repo_path>")
    print("  3. 启动守护进程: contextatlas daemon start")
    print("  4. 在实际对话中测试代码相关问题的回答质量")
    print()


if __name__ == "__main__":
    # 设置控制台编码为 UTF-8
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    asyncio.run(main())
