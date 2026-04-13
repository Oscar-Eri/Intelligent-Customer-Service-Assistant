"""
LLM 功能测试脚本
测试智能体的各项核心功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from LLM.langgraph_engine import create_langgraph_service


async def test_basic_chat():
    """测试基础对话"""
    print("\n" + "="*60)
    print("🧪 测试 1: 基础对话")
    print("="*60)
    
    service = create_langgraph_service()
    
    # 测试问候
    response = await service.chat("你好")
    print(f"👤 用户: 你好")
    print(f"🤖 AI: {response}")
    print()
    
    return service


async def test_time_tools(service):
    """测试时间工具"""
    print("\n" + "="*60)
    print("🧪 测试 2: 时间查询工具")
    print("="*60)
    
    response = await service.chat("现在几点了?")
    print(f"👤 用户: 现在几点了?")
    print(f"🤖 AI: {response}")
    print()


async def test_calculator(service):
    """测试计算器工具"""
    print("\n" + "="*60)
    print("🧪 测试 3: 计算器工具")
    print("="*60)
    
    response = await service.chat("计算 25 * 48 + 100")
    print(f"👤 用户: 计算 25 * 48 + 100")
    print(f"🤖 AI: {response}")
    print()


async def test_weather(service):
    """测试天气查询"""
    print("\n" + "="*60)
    print("🧪 测试 4: 天气查询工具")
    print("="*60)
    
    response = await service.chat("北京今天天气怎么样?")
    print(f"👤 用户: 北京今天天气怎么样?")
    print(f"🤖 AI: {response[:200]}...")
    print()


async def test_sentiment_analysis(service):
    """测试情感分析"""
    print("\n" + "="*60)
    print("🧪 测试 5: 情感分析功能")
    print("="*60)
    
    response = await service.chat("这个产品真的太好用了,我非常喜欢!")
    print(f"👤 用户: 这个产品真的太好用了,我非常喜欢!")
    print(f"🤖 AI: {response}")
    print()
    
    # 检查情感分析结果是否保存
    sentiment_log = current_dir / "LLM" / "Memory" / "Date" / "sentiment_log.json"
    if sentiment_log.exists():
        import json
        with open(sentiment_log, 'r', encoding='utf-8') as f:
            logs = json.load(f)
            if logs:
                last_log = logs[-1]
                print(f"💾 情感日志已保存:")
                print(f"   - 情感倾向: {last_log.get('sentiment_label')}")
                print(f"   - 情感得分: {last_log.get('sentiment_score')}")
                print(f"   - 意图: {last_log.get('intent_result', {}).get('analyzed')}")
    print()


async def test_knowledge_search(service):
    """测试知识库检索"""
    print("\n" + "="*60)
    print("🧪 测试 6: 知识库检索(ContextAtlas)")
    print("="*60)
    
    response = await service.chat("情感分析功能是如何实现的?")
    print(f"👤 用户: 情感分析功能是如何实现的?")
    print(f"🤖 AI: {response[:300]}...")
    print()


async def test_memory_persistence(service):
    """测试记忆持久化"""
    print("\n" + "="*60)
    print("🧪 测试 7: 记忆持久化")
    print("="*60)
    
    # 第一次对话
    await service.chat("我喜欢运动风格的手表")
    print(f"👤 用户: 我喜欢运动风格的手表")
    print(f"   (消息已保存到记忆)")
    
    # 第二次对话,测试是否能记住
    response = await service.chat("你有什么推荐?")
    print(f"👤 用户: 你有什么推荐?")
    print(f"🤖 AI: {response}")
    print()
    
    # 检查记忆文件
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    memory_file = current_dir / "LLM" / "Memory" / "Date" / f"{today}.json"
    
    if memory_file.exists():
        import json
        with open(memory_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"💾 记忆文件状态:")
            print(f"   - 日期: {data.get('date')}")
            print(f"   - 对话数量: {data.get('message_count')}")
            print(f"   - 总结长度: {len(data.get('summary', ''))} 字")
    print()


async def test_stream_output():
    """测试流式输出"""
    print("\n" + "="*60)
    print("🧪 测试 8: 流式输出")
    print("="*60)
    
    service = create_langgraph_service()
    
    print(f"👤 用户: 给我讲一个简短的故事")
    print(f"🤖 AI: ", end="", flush=True)
    
    async for chunk in service.chat_stream("给我讲一个简短的故事"):
        print(chunk, end="", flush=True)
    
    print("\n")


async def main():
    """主测试函数"""
    print("\n" + "🚀"*30)
    print("开始 LLM 功能测试")
    print("🚀"*30)
    
    try:
        # 测试基础对话并获取服务实例
        service = await test_basic_chat()
        
        # 使用同一个服务实例测试其他功能
        await test_time_tools(service)
        await test_calculator(service)
        await test_weather(service)
        await test_sentiment_analysis(service)
        await test_knowledge_search(service)
        await test_memory_persistence(service)
        await test_stream_output()
        
        print("\n" + "✅"*30)
        print("所有测试完成!")
        print("✅"*30 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
