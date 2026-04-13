"""
【功能】关键词上下文提取（来自cntext的word_in_context函数）

【用途】
- 在文本中查找关键词出现的上下文
- 返回关键词及其周围的词语窗口
- 用于理解用户提到某个问题时的具体语境

【使用示例】
    from 零件.关键词上下文提取 import word_in_context
    
    text = "我想投诉你们的物流服务，快递太慢了"
    result = word_in_context(text, keywords=['投诉', '物流'], window=3)
    
    # 返回DataFrame:
    #   keyword | context
    #   投诉    | 我想投诉你们的物流
    #   物流    | 投诉你们的物流服务

【参数说明】
- text: 待分析的文本
- keywords: 要查找的关键词列表
- window: 上下文窗口大小（默认3，表示前后各取3个词）
- lang: 语言类型 ('chinese' 或 'english')

【返回值】
- pandas DataFrame，包含keyword和context两列

【原始来源】
- cntext库: cntext/stats/utils.py 第99-137行
- 函数名: word_in_context()
"""
import jieba
import pandas as pd
from typing import List


def word_in_context(text: str, keywords: List[str], window: int = 3, lang: str = 'chinese') -> pd.DataFrame:
    """
    在text中查找keywords出现的上下文内容(窗口window)，返回df。
    
    Args:
        text (str): 待分析文本
        keywords (list): 关键词列表
        window (int): 关键词上下文窗口大小
        lang (str, optional): 文本的语言类型，中文chinese、英文english，默认chinese

    Returns:
        pandas.DataFrame: 包含keyword和context两列
    """
    if lang == 'chinese':
        words = jieba.lcut(text.lower())
    elif lang == 'english':
        try:
            from nltk.tokenize import word_tokenize
            words = word_tokenize(text.lower())
        except:
            words = text.lower().split(' ')
    else:
        raise ValueError("lang参数只支持chinese和english")
    
    keywords = [w.lower() for w in keywords]
    
    # 找到每个关键词出现的所有位置
    kw_idxss = [[i for i, x in enumerate(words) if x == keyword] for keyword in keywords]
    
    rows = []
    for keyword, kw_idxs in zip(keywords, kw_idxss):
        for idx in kw_idxs:
            half = int((window - 1) / 2)
            start = max(0, idx - half)
            end = min(len(words), idx + half + 1)
            
            row = {
                'keyword': keyword,
                'context': ''.join(words[start:end]) if lang == 'chinese' else ' '.join(words[start:end])
            }
            rows.append(row)
    
    df = pd.DataFrame(rows)
    return df


if __name__ == '__main__':
    # 测试
    print("=" * 70)
    print("关键词上下文提取测试".center(60))
    print("=" * 70 + "\n")
    
    text = "我想投诉你们的物流服务，快递太慢了，而且包裹还损坏了"
    keywords = ['投诉', '物流', '快递', '包裹']
    
    print(f"文本: {text}\n")
    print(f"查找关键词: {keywords}\n")
    
    result = word_in_context(text, keywords, window=5)
    
    print("提取结果:")
    print(result.to_string(index=False))
