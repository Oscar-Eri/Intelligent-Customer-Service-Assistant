"""
快速测试新增的cntext功能
直接调用工具函数进行测试，无需启动完整服务
"""
import sys
from pathlib import Path

# 添加项目路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from backendtest.LLM.tools import analyze_intent, extract_keywords, extract_entities


def test_new_features():
    """测试新增功能"""
    print("=" * 60)
    print("🧪 测试新增的cntext功能")
    print("=" * 60)
    
    # 测试用例
    test_cases = [
        "我想退货，这个产品质量太差了！",
        "请帮我查询北京明天的天气",
        "张三在上海的阿里巴巴公司工作，非常开心",
        "推荐一款性价比高的笔记本电脑",
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试 {i}: {text}")
        print(f"{'-'*60}")
        
        # 测试意图识别
        try:
            intent_result = analyze_intent(text)
            print(f"\n{intent_result}")
        except Exception as e:
            print(f"❌ 意图识别失败: {e}")
        
        # 测试关键词提取
        try:
            keywords_result = extract_keywords(text)
            print(f"\n{keywords_result}")
        except Exception as e:
            print(f"❌ 关键词提取失败: {e}")
        
        # 测试实体抽取
        try:
            entities_result = extract_entities(text)
            print(f"\n{entities_result}")
        except Exception as e:
            print(f"❌ 实体抽取失败: {e}")
    
    print(f"\n{'='*60}")
    print("✅ 所有测试完成！")
    print(f"{'='*60}")


if __name__ == "__main__":
    test_new_features()
