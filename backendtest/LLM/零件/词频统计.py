"""
【功能】词频统计（来自cntext的word_count函数）

【用途】
- 统计文本中每个词出现的频率
- 自动去除停用词
- 用于发现文本中的高频关键词

【使用示例】
    from 零件.词频统计 import word_count
    
    text = "这个产品质量很好，但是物流太慢了"
    
    # 方式1: 返回Counter对象
    result = word_count(text, return_df=False)
    print(result)  # Counter({'产品': 1, '质量': 1, ...})
    
    # 方式2: 返回DataFrame
    df = word_count(text, return_df=True)
    print(df)
    #      word  freq
    #   0  产品     1
    #   1  质量     1

【参数说明】
- text: 待分析的文本
- lang: 语言类型 ('chinese' 或 'english')
- return_df: 是否返回DataFrame格式（默认False，返回Counter）

【返回值】
- return_df=False: collections.Counter对象
- return_df=True: pandas DataFrame (word, freq两列)

【原始来源】
- cntext库: cntext/stats/utils.py 第69-94行
- 函数名: word_count()
"""
import jieba
import pandas as pd
from collections import Counter
from typing import Union


# 简单中文停用词表
STOPWORDS_ZH = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', 
    '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', 
    '没有', '看', '好', '自己', '这', '他', '她', '它', '们', '那', '些',
    '什么', '怎么', '如何', '哪里', '谁', '哪', '这个', '那个', '这些', '那些'
}

# 简单英文停用词表
STOPWORDS_EN = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'can', 'shall', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'out', 'off', 'over',
    'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'both', 'each', 'few', 'more', 'most',
    'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
    'so', 'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because',
    'until', 'while', 'although', 'though', 'after', 'before', 'i', 'me',
    'my', 'myself', 'we', 'our', 'ours', 'you', 'your', 'he', 'him', 'his'
}


def word_count(text: str, lang: str = 'chinese', return_df: bool = False) -> Union[Counter, pd.DataFrame]:
    """
    统计文本中的词频
    
    Args:
        text (str): 待分析的文本数据
        lang (str, optional): 文本的语言；支持中英文，默认为chinese
        return_df (bool, optional): 返回结果是否为dataframe，默认False

    Returns:
        Counter or DataFrame: 词频统计结果
    """
    # 分词并去除停用词
    if lang == 'chinese':
        words = list(jieba.cut(text))
        words = [w for w in words if w not in STOPWORDS_ZH and len(w.strip()) > 0]
    else:  # english
        words = text.lower().split(" ")
        words = [w for w in words if w not in STOPWORDS_EN and len(w.strip()) > 0]
    
    # 统计词频
    word_freq = Counter(words)
    
    if return_df:
        return pd.DataFrame(word_freq.items(), columns=['word', 'freq'])
    else:
        return word_freq


if __name__ == '__main__':
    # 测试
    print("=" * 70)
    print("词频统计测试".center(60))
    print("=" * 70 + "\n")
    
    text = "这个产品质量很好，但是物流太慢了，客服态度也不怎么样，希望能改进"
    
    print(f"文本: {text}\n")
    
    # 方式1: Counter
    print("【方式1: Counter对象】")
    result = word_count(text, lang='chinese', return_df=False)
    print(f"Top 10 高频词:")
    for word, freq in result.most_common(10):
        print(f"  {word}: {freq}次")
    
    print("\n【方式2: DataFrame】")
    df = word_count(text, lang='chinese', return_df=True)
    print(df.head(10).to_string(index=False))
