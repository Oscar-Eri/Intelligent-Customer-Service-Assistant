"""
测试增强版情感分析器
"""
import sys
import os
# 直接导入当前目录的模块
sys.path.insert(0, os.path.dirname(__file__))

from sentiment_analyzer import SentimentAnalyzer

def test_basic_analysis():
    """测试基础分析"""
    print("=" * 60)
    print("1. 基础词典分析（不考虑上下文）")
    print("=" * 60)
    
    analyzer = SentimentAnalyzer()
    
    text = "这个产品很好用，我非常喜欢"
    result = analyzer.analyze(text, use_context=False)
    
    print(f"\n文本: {text}")
    print(f"方法: {result['method']}")
    print(f"结果: {result['label_cn']} (得分: {result['score']})")
    print(f"置信度: {result['confidence']}")
    print(f"原因: {result['reason']}")


def test_context_analysis():
    """测试考虑上下文的分析"""
    print("\n" + "=" * 60)
    print("2. 增强分析（考虑否定词和程度副词）")
    print("=" * 60)
    
    analyzer = SentimentAnalyzer()
    
    test_cases = [
        "这个产品非常好用，我非常喜欢",
        "这个产品不好用，我不喜欢",
        "这个产品非常不好用，我极其讨厌",
        "价格有点贵，但质量还不错"
    ]
    
    for text in test_cases:
        result = analyzer.analyze(text, use_context=True)
        
        print(f"\n文本: {text}")
        print(f"  方法: {result['method']}")
        print(f"  结果: {result['emoji']} {result['label_cn']} (得分: {result['score']})")
        print(f"  置信度: {result['confidence']}")
        if 'weighted_scores' in result:
            print(f"  加权得分: 正面{result['weighted_scores']['positive']}, 负面{result['weighted_scores']['negative']}")
        if 'negation_count' in result:
            print(f"  否定词数: {result['negation_count']}")
        print(f"  原因: {result['reason']}")


def test_comparison():
    """对比基础分析和增强分析的差异"""
    print("\n" + "=" * 60)
    print("3. 方法对比：有无上下文处理的差异")
    print("=" * 60)
    
    analyzer = SentimentAnalyzer()
    
    text = "这不是一个不好的产品，但也不是特别好"
    
    print(f"\n文本: {text}\n")
    
    # 基础分析
    result1 = analyzer.analyze(text, use_context=False)
    print("【基础分析】")
    print(f"  结果: {result1['label_cn']} (得分: {result1['score']})")
    print(f"  匹配词: 正面{len(result1.get('matched_words', {}).get('positive', []))}个, "
          f"负面{len(result1.get('matched_words', {}).get('negative', []))}个")
    print(f"  原因: {result1['reason']}")
    
    # 增强分析
    result2 = analyzer.analyze(text, use_context=True)
    print("\n【增强分析（考虑否定词）】")
    print(f"  结果: {result2['label_cn']} (得分: {result2['score']})")
    print(f"  加权得分: 正面{result2.get('weighted_scores', {}).get('positive', 0)}, "
          f"负面{result2.get('weighted_scores', {}).get('negative', 0)}")
    print(f"  否定词数: {result2.get('negation_count', 0)}")
    print(f"  原因: {result2['reason']}")


def test_llm_fallback():
    """测试LLM兜底"""
    print("\n" + "=" * 60)
    print("4. LLM兜底测试")
    print("=" * 60)
    
    analyzer = SentimentAnalyzer()
    
    # 强制使用LLM
    text = "这个产品的用户体验还算可以吧，说不上特别好但也凑合"
    result = analyzer.analyze(text, force_llm=True)
    
    print(f"\n文本: {text}")
    print(f"方法: {result['method']}")
    print(f"结果: {result['emoji']} {result['label_cn']} (得分: {result['score']})")
    print(f"置信度: {result['confidence']}")
    if 'reason' in result:
        print(f"理由: {result['reason']}")


if __name__ == '__main__':
    print("\n" + "🎯 增强版情感分析器测试".center(60, "="))
    
    try:
        test_basic_analysis()
        test_context_analysis()
        test_comparison()
        test_llm_fallback()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        print("\n核心功能:")
        print("1. ✓ 独立实现（不依赖cntext模块）")
        print("2. ✓ 本地词典数据（27,237个情感词）")
        print("3. ✓ 否定词处理（不、没、别等）")
        print("4. ✓ 程度副词加权（非常、很、稍微等）")
        print("5. ✓ LLM兜底机制")
        
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
