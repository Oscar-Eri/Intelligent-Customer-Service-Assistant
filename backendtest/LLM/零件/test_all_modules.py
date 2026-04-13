"""
零件模块完整功能测试
验证所有5个模块的功能完整性
"""
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_关键词上下文提取():
    """测试关键词上下文提取模块"""
    print("=" * 70)
    print("测试1: 关键词上下文提取".center(60))
    print("=" * 70)
    
    from 零件.关键词上下文提取 import word_in_context
    
    text = "我想投诉你们的物流服务，快递太慢了，而且包裹还损坏了"
    keywords = ['投诉', '物流', '快递', '包裹']
    
    result = word_in_context(text, keywords, window=5)
    
    print(f"✓ 输入文本: {text}")
    print(f"✓ 查找关键词: {keywords}")
    print(f"✓ 提取结果: {len(result)} 条记录")
    print(f"✓ 返回类型: {type(result)}")
    print(f"✓ 列名: {list(result.columns)}")
    print("\n详细结果:")
    print(result.to_string(index=False))
    print()
    
    assert len(result) == 4, "应该找到4个关键词"
    assert 'keyword' in result.columns, "应该有keyword列"
    assert 'context' in result.columns, "应该有context列"
    
    print("✅ 关键词上下文提取测试通过!\n")


def test_词频统计():
    """测试词频统计模块"""
    print("=" * 70)
    print("测试2: 词频统计".center(60))
    print("=" * 70)
    
    from 零件.词频统计 import word_count
    
    text = "这个产品质量很好，但是物流太慢了，客服态度也不怎么样"
    
    # 测试Counter模式
    result_counter = word_count(text, lang='chinese', return_df=False)
    print(f"✓ 输入文本: {text}")
    print(f"✓ Counter模式: {len(result_counter)} 个不同词汇")
    print(f"✓ Top 5: {result_counter.most_common(5)}")
    
    # 测试DataFrame模式
    result_df = word_count(text, lang='chinese', return_df=True)
    print(f"✓ DataFrame模式: {len(result_df)} 行")
    print(f"✓ 列名: {list(result_df.columns)}")
    print("\n详细结果:")
    print(result_df.head(10).to_string(index=False))
    print()
    
    assert len(result_counter) > 0, "应该有词频统计结果"
    assert len(result_df) > 0, "DataFrame应该有数据"
    assert 'word' in result_df.columns, "应该有word列"
    assert 'freq' in result_df.columns, "应该有freq列"
    
    print("✅ 词频统计测试通过!\n")


def test_句子分割():
    """测试句子分割模块"""
    print("=" * 70)
    print("测试3: 句子分割".center(60))
    print("=" * 70)
    
    from 零件.句子分割 import zh_split_sentences
    
    text = "这个产品很好。但是物流太慢了！客服态度不错？"
    
    sentences = zh_split_sentences(text)
    
    print(f"✓ 输入文本: {text}")
    print(f"✓ 分割结果: {len(sentences)} 个句子")
    print(f"✓ 返回类型: {type(sentences)}")
    for i, sent in enumerate(sentences, 1):
        print(f"  {i}. {sent}")
    print()
    
    assert len(sentences) == 3, f"应该分割为3个句子，实际{len(sentences)}个"
    assert isinstance(sentences, list), "应该返回列表"
    
    print("✅ 句子分割测试通过!\n")


def test_文本清洗():
    """测试文本清洗模块"""
    print("=" * 70)
    print("测试4: 文本清洗".center(60))
    print("=" * 70)
    
    from 零件.文本清洗 import clean_text, traditional_to_simplified, fix_fullwidth_to_halfwidth
    
    # 测试1: 基础清洗
    dirty_text = "  这个   产品  很好  ，  但是  物流  太慢  了  "
    cleaned = clean_text(dirty_text, lang='chinese')
    print(f"✓ 基础清洗:")
    print(f"  原文: '{dirty_text}'")
    print(f"  清洗后: '{cleaned}'")
    
    # 测试2: 繁体转简体
    trad_text = "這個產品質量很好"
    simple_text = traditional_to_simplified(trad_text)
    print(f"\n✓ 繁体转简体:")
    print(f"  繁体: {trad_text}")
    print(f"  简体: {simple_text}")
    
    # 测试3: 全角转半角
    fullwidth_text = "ｈｅｌｌｏ　ｗｏｒｌｄ！１２３"
    halfwidth_text = fix_fullwidth_to_halfwidth(fullwidth_text)
    print(f"\n✓ 全角转半角:")
    print(f"  全角: {fullwidth_text}")
    print(f"  半角: {halfwidth_text}")
    print()
    
    assert cleaned == "这个产品很好，但是物流太慢了", f"清洗结果不正确: {cleaned}"
    assert simple_text == "这个产品质量很好", f"繁简转换不正确: {simple_text}"
    assert halfwidth_text == "hello world!123", f"全角转换不正确: {halfwidth_text}"
    
    print("✅ 文本清洗测试通过!\n")


def test_文本相似度():
    """测试文本相似度模块"""
    print("=" * 70)
    print("测试5: 文本相似度".center(60))
    print("=" * 70)
    
    from 零件.文本相似度 import (
        cosine_sim, jaccard_sim, minedit_sim, 
        simple_sim, find_most_similar, batch_similarity
    )
    
    text1 = "我要退款"
    text2 = "退款流程是什么"
    text3 = "物流查询"
    
    # 测试1: 余弦相似度
    sim_cosine = cosine_sim(text1, text2)
    print(f"✓ 余弦相似度:")
    print(f"  '{text1}' vs '{text2}': {sim_cosine}")
    
    # 测试2: Jaccard相似度
    sim_jaccard = jaccard_sim(text1, text2)
    print(f"\n✓ Jaccard相似度:")
    print(f"  '{text1}' vs '{text2}': {sim_jaccard}")
    
    # 测试3: 编辑距离相似度
    sim_minedit = minedit_sim(text1, text2)
    print(f"\n✓ 编辑距离相似度:")
    print(f"  '{text1}' vs '{text2}': {sim_minedit}")
    
    # 测试4: 简单相似度
    sim_simple = simple_sim(text1, text2)
    print(f"\n✓ 简单相似度:")
    print(f"  '{text1}' vs '{text2}': {sim_simple}")
    
    # 测试5: 批量查找最相似
    candidates = ["如何退款", "怎么改地址", "物流查询"]
    result = find_most_similar("我要退钱", candidates, method='jaccard')
    print(f"\n✓ 批量查找最相似:")
    print(f"  查询: '我要退钱'")
    print(f"  最佳匹配: {result['best_match']} (相似度: {result['similarity']})")
    print(f"  所有结果: {len(result['all_scores'])} 个")
    
    # 测试6: 批量相似度矩阵
    texts = [text1, text2, text3]
    matrix_result = batch_similarity(texts, method='minedit')
    print(f"\n✓ 批量相似度矩阵:")
    print(f"  文本数: {len(matrix_result['texts'])}")
    print(f"  矩阵大小: {len(matrix_result['matrix'])}x{len(matrix_result['matrix'][0])}")
    print(f"  方法: {matrix_result['method']}")
    print(f"  矩阵:")
    for i, row in enumerate(matrix_result['matrix']):
        print(f"    {row}")
    print()
    
    assert 0 <= sim_cosine <= 1, "余弦相似度应该在0-1之间"
    assert 0 <= sim_jaccard <= 1, "Jaccard相似度应该在0-1之间"
    assert 0 <= sim_minedit <= 1, "编辑距离相似度应该在0-1之间"
    assert result['best_match'] is not None, "应该找到最佳匹配"
    assert len(matrix_result['matrix']) == 3, "矩阵应该是3x3"
    
    print("✅ 文本相似度测试通过!\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("零件模块完整功能测试".center(60))
    print("=" * 70 + "\n")
    
    try:
        test_关键词上下文提取()
        test_词频统计()
        test_句子分割()
        test_文本清洗()
        test_文本相似度()
        
        print("=" * 70)
        print("🎉 所有测试通过！".center(60))
        print("=" * 70)
        print("\n✅ 零件模块功能完整且可用！")
        print("\n可用模块:")
        print("  1. 关键词上下文提取 - word_in_context()")
        print("  2. 词频统计 - word_count()")
        print("  3. 句子分割 - zh_split_sentences()")
        print("  4. 文本清洗 - clean_text(), traditional_to_simplified()")
        print("  5. 文本相似度 - cosine_sim(), jaccard_sim(), minedit_sim()")
        print("     - find_most_similar() - 批量查找")
        print("     - batch_similarity() - 相似度矩阵")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
