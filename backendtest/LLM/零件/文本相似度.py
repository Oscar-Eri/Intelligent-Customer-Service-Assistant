"""
【功能】文本相似度计算（来自cntext的similarity模块）

【用途】
- 计算两段文本的相似程度
- 用于FAQ匹配、问题去重、相似内容推荐
- 提供4种算法：余弦相似度、Jaccard、编辑距离、简单diff

【使用示例】
    from 零件.文本相似度 import cosine_sim, find_most_similar
    
    # 示例1: 计算两个文本的相似度
    sim = cosine_sim("我要退款", "如何申请退货")
    print(sim)  # 0.0 (因为没有共同词汇)
    
    # 示例2: 有共同词汇的情况
    sim = cosine_sim("我要退款", "退款流程是什么")
    print(sim)  # 0.58 (有共同词"退款")
    
    # 示例3: 从 FAQ库中找最匹配的问题
    faqs = ["如何退款", "怎么改地址", "物流查询"]
    result = find_most_similar("我要退钱", faqs, method='cosine')
    print(result['best_match'])  # "如何退款"
    print(result['similarity'])  # 相似度分数

【提供的函数】
1. cosine_sim(text1, text2) - 余弦相似度 (基于词频向量)
2. jaccard_sim(text1, text2) - Jaccard集合相似度 (基于词集交集/并集)
3. minedit_sim(text1, text2) - 编辑距离相似度 (基于字符序列)
4. simple_sim(text1, text2) - 简单diff相似度
5. find_most_similar(query, candidates) - 批量查找最相似
6. batch_similarity(texts) - 批量计算所有文本对的相似度矩阵

【重要说明】
- 余弦相似度基于词频向量，如果两个文本没有共同词汇，相似度为0
- 对于语义相似但用词不同的文本，建议使用Embedding模型（如BERT）
- Jaccard和编辑距离对短文本效果更好
- minedit_sim使用字符级别比较，适合中文

【原始来源】
- cntext库: cntext/stats/similarity.py 第1-138行
- 函数名: cosine_sim, jaccard_sim, minedit_sim, simple_sim
"""
import jieba
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher, Differ
from typing import List


def _transform(text1: str, text2: str, lang: str = 'chinese'):
    """文本向量化预处理（内部函数）"""
    if lang == 'chinese':
        text1_processed = ' '.join(list(jieba.cut(text1)))
        text2_processed = ' '.join(list(jieba.cut(text2)))
    elif lang == 'english':
        text1_processed = text1.lower()
        text2_processed = text2.lower()
    else:
        raise ValueError('lang must be chinese or english.')
    
    corpus = [text1_processed, text2_processed]
    # 设置min_df=1以包含所有词
    cv = CountVectorizer(min_df=1)
    vec_matrix = cv.fit_transform(corpus)
    vec1 = vec_matrix[0].toarray()
    vec2 = vec_matrix[1].toarray()
    
    return text1_processed, text2_processed, vec1, vec2


def cosine_sim(text1: str, text2: str, lang: str = 'chinese') -> float:
    """
    余弦相似度算法（推荐）
    
    原理：将文本转换为向量，计算两个向量夹角的余弦值
    范围：0-1，越接近1表示越相似
    
    Args:
        text1: 文本1
        text2: 文本2
        lang: 语言类型 ('chinese' 或 'english')
    
    Returns:
        float: 相似度分数 (0-1)
    """
    _, _, vec1, vec2 = _transform(text1, text2, lang=lang)
    similarity = cosine_similarity(vec1, vec2)[0][0]
    return round(float(similarity), 2)


def jaccard_sim(text1: str, text2: str, lang: str = 'chinese') -> float:
    """
    Jaccard相似度算法
    
    原理：计算两个文本词集的交集与并集之比
    公式：|A∩B| / |A∪B|
    范围：0-1，越接近1表示越相似
    
    Args:
        text1: 文本1
        text2: 文本2
        lang: 语言类型
    
    Returns:
        float: 相似度分数 (0-1)
    """
    # 直接分词计算，不使用向量化
    if lang == 'chinese':
        words1 = set(jieba.cut(text1))
        words2 = set(jieba.cut(text2))
    else:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
    
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    if union == 0:
        return 0.0
    
    similarity = intersection / union
    return round(similarity, 2)


def minedit_sim(text1: str, text2: str, lang: str = 'chinese') -> float:
    """
    最小编辑距离相似度
    
    原理：计算将一个文本转换为另一个文本所需的最少编辑操作次数
    范围：0-1，越接近1表示越相似
    
    Args:
        text1: 文本1
        text2: 文本2
        lang: 语言类型
    
    Returns:
        float: 相似度分数 (0-1)
    """
    if lang == 'chinese':
        # 使用字符级别比较（更准确）
        seq1 = list(text1)
        seq2 = list(text2)
    elif lang == 'english':
        seq1 = text1.lower().split()
        seq2 = text2.lower().split()
    else:
        raise ValueError('lang must be chinese or english.')
    
    matcher = SequenceMatcher(None, seq1, seq2)
    similarity = matcher.ratio()  # 直接使用ratio()
    
    return round(similarity, 2)


def simple_sim(text1: str, text2: str, lang: str = 'chinese') -> float:
    """
    简单相似度算法（基于diff）
    
    原理：参考Unix diff命令，计算文本差异比例
    范围：0-1，越接近1表示越相似
    
    Args:
        text1: 文本1
        text2: 文本2
        lang: 语言类型
    
    Returns:
        float: 相似度分数 (0-1)
    """
    if lang == 'chinese':
        words1 = list(jieba.cut(text1))
        words2 = list(jieba.cut(text2))
    elif lang == 'english':
        words1 = text1.lower().split()
        words2 = text2.lower().split()
    else:
        raise ValueError('lang must be chinese or english.')
    
    differ = Differ()
    diff_result = list(differ.compare(words1, words2))
    
    diff_ratio = len(diff_result) / (len(words1) + len(words2))
    
    max_len = max(len(words1), len(words2))
    if max_len == 0:
        return 1.0
    
    similarity = (max_len - diff_ratio) / max_len
    return round(max(0.0, similarity), 2)


def batch_similarity(texts: List[str], method: str = 'cosine') -> dict:
    """
    批量计算所有文本对的相似度矩阵
    
    Args:
        texts: 文本列表
        method: 相似度算法 ('cosine', 'jaccard', 'minedit', 'simple')
    
    Returns:
        dict: {
            'matrix': 相似度矩阵 (二维列表),
            'texts': 原始文本列表,
            'method': 使用的算法
        }
    
    Example:
        >>> texts = ["我要退款", "怎么退货", "物流查询"]
        >>> result = batch_similarity(texts, method='jaccard')
        >>> print(result['matrix'])
        [[1.0, 0.5, 0.0],
         [0.5, 1.0, 0.0],
         [0.0, 0.0, 1.0]]
    """
    sim_functions = {
        'cosine': cosine_sim,
        'jaccard': jaccard_sim,
        'minedit': minedit_sim,
        'simple': simple_sim
    }
    
    if method not in sim_functions:
        raise ValueError(f"Unsupported method: {method}")
    
    sim_func = sim_functions[method]
    n = len(texts)
    
    # 初始化相似度矩阵
    matrix = [[0.0] * n for _ in range(n)]
    
    # 计算所有文本对的相似度
    for i in range(n):
        for j in range(i, n):
            if i == j:
                matrix[i][j] = 1.0  # 自身相似度为1
            else:
                sim = sim_func(texts[i], texts[j])
                matrix[i][j] = sim
                matrix[j][i] = sim  # 对称矩阵
    
    return {
        'matrix': matrix,
        'texts': texts,
        'method': method
    }


def find_most_similar(query: str, candidates: List[str], method: str = 'cosine') -> dict:
    """
    从候选列表中找到最相似的文本
    
    Args:
        query: 查询文本
        candidates: 候选文本列表
        method: 相似度算法 ('cosine', 'jaccard', 'minedit', 'simple')
    
    Returns:
        dict: {
            'best_match': 最匹配的文本,
            'similarity': 相似度分数,
            'all_scores': 所有候选的相似度列表
        }
    """
    sim_functions = {
        'cosine': cosine_sim,
        'jaccard': jaccard_sim,
        'minedit': minedit_sim,
        'simple': simple_sim
    }
    
    if method not in sim_functions:
        raise ValueError(f"Unsupported method: {method}")
    
    sim_func = sim_functions[method]
    
    scores = []
    for candidate in candidates:
        score = sim_func(query, candidate)
        scores.append({
            'text': candidate,
            'similarity': score
        })
    
    scores.sort(key=lambda x: x['similarity'], reverse=True)
    
    return {
        'best_match': scores[0]['text'] if scores else None,
        'similarity': scores[0]['similarity'] if scores else 0.0,
        'all_scores': scores
    }


if __name__ == '__main__':
    # 测试
    print("=" * 70)
    print("文本相似度计算测试".center(60))
    print("=" * 70 + "\n")
    
    test_pairs = [
        ("这个产品很好", "产品质量不错"),
        ("我要退款", "如何申请退货"),
        ("快递太慢了", "物流配送速度慢"),
        ("服务态度好", "客服很热情"),
        ("完全无关的文本", "另一个话题的内容")
    ]
    
    for text1, text2 in test_pairs:
        print(f"文本1: {text1}")
        print(f"文本2: {text2}")
        print(f"  余弦相似度: {cosine_sim(text1, text2)}")
        print(f"  Jaccard相似度: {jaccard_sim(text1, text2)}")
        print(f"  编辑距离相似度: {minedit_sim(text1, text2)}")
        print()
    
    # FAQ匹配示例
    print("\n" + "=" * 70)
    print("FAQ匹配示例".center(60))
    print("=" * 70 + "\n")
    
    faq_database = [
        "如何申请退款？",
        "怎么修改订单地址？",
        "物流信息查询方法",
        "如何联系客服？",
        "退换货政策说明"
    ]
    
    user_question = "我要退钱"
    
    print(f"用户问题: {user_question}\n")
    print("FAQ匹配结果:")
    
    result = find_most_similar(user_question, faq_database, method='cosine')
    print(f"  最佳匹配: {result['best_match']}")
    print(f"  相似度: {result['similarity']}")
    print(f"\n  所有匹配:")
    for item in result['all_scores']:
        print(f"    - {item['text']}: {item['similarity']}")
