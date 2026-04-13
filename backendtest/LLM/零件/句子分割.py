"""
【功能】中文句子分割（来自cntext的zh_split_sentences函数）

【用途】
- 将长文本按句子分割成列表
- 支持中文标点符号（。！？；?）
- 用于句子级情感分析、逐句处理

【使用示例】
    from 零件.句子分割 import zh_split_sentences
    
    text = "这个产品很好。但是物流太慢了！客服态度不错？"
    sentences = zh_split_sentences(text)
    
    print(sentences)
    # ['这个产品很好', '但是物流太慢了', '客服态度不错']

【参数说明】
- text: 待分句的中文文本

【返回值】
- list: 句子列表

【原始来源】
- cntext库: cntext/stats/utils.py 第32-48行
- 函数名: zh_split_sentences()
"""
import re


def zh_split_sentences(text: str) -> list:
    """
    将中文文本分割为句子
    
    Args:
        text (str): 待分句的中文文本
        
    Returns:
        list: 句子列表
    """
    # 1. 以句号、感叹号、问号、分号分句
    text = re.sub(r'([。！；？;\?])([^"\'])', r"\1[[end]]\2", text)
    text = re.sub(r'([。！？\?]["\'])([^，。！？\?])', r"\1[[end]]\2", text)
    
    # 2. 去除空白字符
    text = re.sub(r'\s', '', text)
    
    # 3. 分割
    sentences = text.split("[[end]]")
    
    # 4. 过滤空句子
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


if __name__ == '__main__':
    # 测试
    print("=" * 70)
    print("中文句子分割测试".center(60))
    print("=" * 70 + "\n")
    
    test_texts = [
        "这个产品很好。但是物流太慢了！客服态度不错？",
        "质量优秀，包装精美。快递速度快，服务态度好。",
        "第一次购买体验很差！产品质量有问题，而且客服不理人。非常失望！",
    ]
    
    for text in test_texts:
        print(f"原文: {text}")
        sentences = zh_split_sentences(text)
        print(f"分割结果 ({len(sentences)}个句子):")
        for i, sent in enumerate(sentences, 1):
            print(f"  {i}. {sent}")
        print()
