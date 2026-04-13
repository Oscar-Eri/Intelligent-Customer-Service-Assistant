"""
纯 LLM 情感分析测试
仅使用通义千问 API 进行情感判断，不依赖 cntext 词典
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from backendtest.LLM.tools import analyze_emotion


async def test_llm_emotion_analysis():
    """测试纯 LLM 情感分析功能"""
    print("=" * 60)
    print("🧪 纯 LLM 情感分析测试")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        ("你好，今天天气真好！", "正面情感"),
        ("这个产品太糟糕了，我很失望。", "负面情感"),
        ("请帮我查询一下北京的天气。", "中性情感"),
        ("我非常开心，今天完成了一个重要项目！", "强烈正面情感"),
        ("真的很生气，服务态度太差了！", "强烈负面情感"),
        ("有点担心明天的面试结果。", "焦虑/恐惧情感"),
        ("哇！这个惊喜太棒了！", "惊讶情感"),
        ("这部电影真让人恶心。", "厌恶情感"),
    ]
    
    for i, (user_input, description) in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {description}")
        print(f"用户输入: {user_input}")
        print(f"{'-'*60}")
        
        try:
            # 调用 LLM 情感分析工具（同步调用）
            result = analyze_emotion(user_input)
            
            print(f"\n{result}")
            print(f"\n✅ 测试 {i} 通过")
            
        except Exception as e:
            print(f"❌ 测试 {i} 失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 短暂延迟，避免请求过快
        import time
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print("🎉 所有测试完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(test_llm_emotion_analysis())
