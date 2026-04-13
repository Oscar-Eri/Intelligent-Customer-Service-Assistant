"""
【零件模块】来自cntext的独立功能组件

本文件夹包含从cntext库中提取的独立功能模块，每个文件都是自包含的，
可以单独使用，无需依赖cntext库。

【可用模块】
1. 关键词上下文提取 - word_in_context()
2. 词频统计 - word_count()
3. 文本相似度 - cosine_sim(), jaccard_sim(), find_most_similar()
4. 句子分割 - zh_split_sentences()
5. 文本清洗 - clean_text(), traditional_to_simplified()

【使用示例】
    from 零件 import word_in_context, word_count, cosine_sim
    
    # 或者单独导入
    from 零件.关键词上下文提取 import word_in_context
    from 零件.词频统计 import word_count
    from 零件.文本相似度 import cosine_sim
"""

# 导出所有常用函数
from .关键词上下文提取 import word_in_context
from .词频统计 import word_count
from .文本相似度 import cosine_sim, jaccard_sim, minedit_sim, simple_sim, find_most_similar, batch_similarity
from .句子分割 import zh_split_sentences
from .文本清洗 import clean_text, traditional_to_simplified, fix_fullwidth_to_halfwidth

__all__ = [
    'word_in_context',
    'word_count',
    'cosine_sim',
    'jaccard_sim',
    'minedit_sim',
    'simple_sim',
    'find_most_similar',
    'batch_similarity',
    'zh_split_sentences',
    'clean_text',
    'traditional_to_simplified',
    'fix_fullwidth_to_halfwidth',
]
