"""
情感分析模块 - 统一导出接口
现在已拆分为独立的 SentimentAnalyzer 和 IntentAnalyzer
此文件用于保持向后兼容性
"""
from ..emotion.sentiment_analyzer import SentimentAnalyzer
from ..intent.intent_analyzer import IntentAnalyzer

# 导出类，方便外部直接导入
__all__ = ['SentimentAnalyzer', 'IntentAnalyzer']

# 兼容旧代码的快捷函数
def analyze_sentiment(text: str):
    return SentimentAnalyzer().analyze(text)

def analyze_intent(text: str):
    return IntentAnalyzer().analyze(text)
