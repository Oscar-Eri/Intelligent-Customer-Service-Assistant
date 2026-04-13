"""
测试增强版意图识别器
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from intent_analyzer import IntentAnalyzer

def test_dict_based_intent():
    """测试基于词典的意图识别"""
    print("=" * 60)
    print("1. 词典规则意图识别")
    print("=" * 60)
    
    analyzer = IntentAnalyzer()
    
    test_cases = [
        "请问这个产品怎么使用？",
        "我要投诉，服务质量太差了！",
        "非常感谢你们的帮助，很满意",
        "希望能改进一下包装",
        "我要退款，这个订单不要了",
        "快递什么时候能到？"
    ]
    
    for text in test_cases:
        result = analyzer.analyze(text, use_dict=True, use_context=False)
        
        print(f"\n文本: {text}")
        print(f"  意图: {result['intent']}")
        print(f"  置信度: {result['confidence']}")
        print(f"  优先级: {result['priority']}")
        print(f"  需要行动: {result['action_needed']}")
        if 'matched_keywords' in result:
            print(f"  匹配关键词: {result['matched_keywords']}")


def test_keywords_context():
    """测试关键词上下文提取"""
    print("\n" + "=" * 60)
    print("2. 关键词上下文提取(来自cntext)")
    print("=" * 60)
    
    analyzer = IntentAnalyzer()
    
    text = "我想投诉你们的物流服务，快递太慢了，而且包裹还损坏了"
    
    print(f"\n文本: {text}\n")
    
    result = analyzer.analyze(text, use_dict=True, use_context=True)
    
    if 'keywords_context' in result and result['keywords_context']:
        print("提取到的关键词上下文:")
        for ctx in result['keywords_context'][:5]:  # 只显示前5个
            print(f"  关键词: {ctx['keyword']}")
            print(f"  上下文: ...{ctx['context']}...")
            print()


def test_word_frequency():
    """测试词频统计"""
    print("\n" + "=" * 60)
    print("3. 词频统计(来自cntext)")
    print("=" * 60)
    
    analyzer = IntentAnalyzer()
    
    text = "这个产品质量很好，但是物流太慢了，客服态度也不怎么样，希望能改进"
    
    print(f"\n文本: {text}\n")
    
    result = analyzer.analyze(text, use_dict=True, use_context=False)
    
    if 'word_freq' in result:
        print("高频词汇(Top 10):")
        for word, freq in result['word_freq'].items():
            print(f"  {word}: {freq}次")


def test_hybrid_strategy():
    """测试混合策略"""
    print("\n" + "=" * 60)
    print("4. 混合策略:词典优先 + LLM兜底")
    print("=" * 60)
    
    analyzer = IntentAnalyzer()
    
    test_cases = [
        ("明确的投诉", "我要投诉！服务态度太差了！"),
        ("模糊的表达", "这个嘛...怎么说呢...就那样吧"),
        ("复杂的情况", "产品质量还可以，但是物流有点慢，不过客服态度还不错")
    ]
    
    for desc, text in test_cases:
        result = analyzer.analyze(text, use_dict=True, use_context=True)
        
        print(f"\n【{desc}】")
        print(f"文本: {text}")
        print(f"方法: {result.get('method', 'unknown')}")
        print(f"意图: {result['intent']}")
        print(f"置信度: {result['confidence']}")
        print(f"原因: {result.get('reason', 'N/A')}")


def compare_methods():
    """对比纯LLM和混合策略"""
    print("\n" + "=" * 60)
    print("5. 方法对比:纯LLM vs 混合策略")
    print("=" * 60)
    
    analyzer = IntentAnalyzer()
    
    text = "请问如何申请退款？我已经等了三天了"
    
    print(f"\n文本: {text}\n")
    
    # 混合策略
    result1 = analyzer.analyze(text, use_dict=True, use_context=True)
    print("【混合策略(词典+上下文+LLM)】")
    print(f"  方法: {result1['method']}")
    print(f"  意图: {result1['intent']}")
    print(f"  置信度: {result1['confidence']}")
    if 'keywords_context' in result1:
        print(f"  关键词数: {len(result1['keywords_context'])}")
    if 'word_freq' in result1:
        print(f"  高频词: {list(result1['word_freq'].keys())[:5]}")
    
    # 纯LLM
    result2 = analyzer._analyze_with_llm(text)
    print("\n【纯LLM】")
    print(f"  意图: {result2['intent']}")
    print(f"  置信度: {result2['confidence']}")
    print(f"  原因: {result2.get('reason', 'N/A')}")


if __name__ == '__main__':
    print("\n" + "🎯 增强版意图识别器测试".center(60, "="))
    
    try:
        test_dict_based_intent()
        test_keywords_context()
        test_word_frequency()
        test_hybrid_strategy()
        compare_methods()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        print("\n核心功能:")
        print("1. ✓ 词典规则识别(来自cntext思想)")
        print("2. ✓ 关键词上下文提取(来自cntext.word_in_context)")
        print("3. ✓ 词频统计分析(来自cntext.word_count)")
        print("4. ✓ 混合策略:词典优先 + LLM兜底")
        print("5. ✓ 自动判断优先级和行动需求")
        
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
