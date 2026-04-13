"""
用户意图识别模块 (Intent Recognition)
增强版:词典规则 + 关键词上下文 + LLM混合策略
核心特性:
- 关键词上下文提取(来自cntext)
- 词频统计分析(来自cntext)
- 文本相似度匹配(来自cntext)
- LLM兜底机制
"""
import os
import re
import json
from typing import Dict, List
from collections import Counter
import jieba
from langchain_openai import ChatOpenAI

# 支持直接运行和模块导入两种方式
try:
    from ...config import qwen_base_url, qwen_api_key
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from config import qwen_base_url, qwen_api_key


class IntentAnalyzer:
    """增强版意图识别器(基于cntext算法)"""
    
    # 意图关键词词典(来自cntext的词典思想)
    INTENT_KEYWORDS = {
        '咨询': ['请问', '怎么', '如何', '哪里', '什么', '多少', '能否', '可以', '需要', '想要', '了解'],
        '投诉': ['投诉', '不满', '差评', '糟糕', '太差', '生气', '失望', '举报', '维权', '垃圾', '骗子'],
        '表扬': ['感谢', '谢谢', '好评', '满意', '不错', '很好', '优秀', '棒', '赞', '厉害'],
        '建议': ['建议', '希望', '应该', '可以改进', '最好', '如果能', '提个意见'],
        '退款': ['退款', '退货', '退钱', '返还', '取消订单', '不要了'],
        '物流': ['快递', '物流', '配送', '发货', '到货', '运输', '包裹', '邮寄']
    }
    
    def __init__(self):
        # 加载停用词(可选)
        self.stopwords = self._load_stopwords()
        
        # 初始化 LLM(作为兜底)
        self.llm = ChatOpenAI(
            model="qwen-plus",
            base_url=qwen_base_url,
            api_key=qwen_api_key,
            temperature=0,
            max_tokens=200,
        )
    
    def _load_stopwords(self) -> set:
        """加载停用词表"""
        return {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
    
    def analyze(self, text: str, use_dict: bool = True, use_context: bool = True) -> Dict:
        """
        执行意图识别(混合策略)
        
        Args:
            text: 待分析文本
            use_dict: 是否使用词典规则
            use_context: 是否提取关键词上下文
        
        Returns:
            {
                "intent": "咨询/投诉/表扬/建议/退款/物流/其他",
                "confidence": 0.90,
                "action_needed": true/false,
                "priority": "high/medium/low",
                "keywords_context": [...],
                "word_freq": {...}
            }
        """
        result = {}
        
        # 策略1:词典规则分析
        if use_dict:
            dict_result = self._analyze_with_dict(text)
            if dict_result['confidence'] >= 0.7:
                result.update(dict_result)
        
        # 策略2:提取关键词上下文
        if use_context:
            keywords_ctx = self._extract_keywords_context(text)
            result['keywords_context'] = keywords_ctx
        
        # 策略3:词频统计
        word_freq = self._get_word_frequency(text)
        result['word_freq'] = dict(word_freq.most_common(10))
        
        # 如果词典方法置信度低,调用LLM
        if result.get('confidence', 0) < 0.7:
            llm_result = self._analyze_with_llm(text)
            result.update(llm_result)
            result['method'] = 'llm'
        else:
            result['method'] = 'dict_rule'
        
        return result
    
    def _analyze_with_dict(self, text: str) -> Dict:
        """
        基于词典规则的意图识别
        核心思想来自cntext的情感词典方法
        """
        # 分词
        words = list(jieba.cut(text))
        
        # 统计各意图类别的匹配词数
        intent_scores = {}
        matched_keywords = {}
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            matches = [w for w in words if w in keywords]
            if matches:
                intent_scores[intent] = len(matches)
                matched_keywords[intent] = matches
        
        # 如果没有匹配到任何关键词
        if not intent_scores:
            return {
                'intent': '其他',
                'confidence': 0.0,
                'action_needed': False,
                'priority': 'low',
                'reason': '未匹配到意图关键词'
            }
        
        # 找出得分最高的意图
        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]
        total_matches = sum(intent_scores.values())
        
        # 计算置信度
        confidence = min(best_score / total_matches + 0.3, 1.0)
        
        # 判断是否需要行动和优先级
        action_needed, priority = self._get_action_priority(best_intent, best_score)
        
        return {
            'intent': best_intent,
            'confidence': round(confidence, 2),
            'action_needed': action_needed,
            'priority': priority,
            'matched_keywords': matched_keywords,
            'reason': f'匹配到{total_matches}个意图关键词,{best_intent}类{best_score}个'
        }
    
    def _extract_keywords_context(self, text: str, window: int = 5) -> List[Dict]:
        """
        提取关键词的上下文(来自cntext的word_in_context函数)
        
        Args:
            text: 待分析文本
            window: 上下文窗口大小
        
        Returns:
            关键词及其上下文的列表
        """
        # 收集所有意图关键词
        all_keywords = []
        for kws in self.INTENT_KEYWORDS.values():
            all_keywords.extend(kws)
        all_keywords = list(set(all_keywords))
        
        # 查找关键词及其上下文
        contexts = []
        for keyword in all_keywords:
            if keyword in text:
                # 找到关键词位置
                idx = text.find(keyword)
                if idx != -1:
                    # 提取上下文
                    start = max(0, idx - window * 2)
                    end = min(len(text), idx + len(keyword) + window * 2)
                    context = text[start:end]
                    
                    contexts.append({
                        'keyword': keyword,
                        'context': context,
                        'position': idx
                    })
        
        return contexts
    
    def _get_word_frequency(self, text: str) -> Counter:
        """
        词频统计(来自cntext的word_count函数)
        
        Args:
            text: 待分析文本
        
        Returns:
            词频计数器
        """
        # 分词
        words = list(jieba.cut(text))
        
        # 去除停用词和单字符
        words = [w for w in words if w not in self.stopwords and len(w) > 1]
        
        return Counter(words)
    
    def _get_action_priority(self, intent: str, score: int) -> tuple:
        """根据意图类型和得分判断行动需求和优先级"""
        high_priority_intents = ['投诉', '退款']
        medium_priority_intents = ['咨询', '物流']
        
        if intent in high_priority_intents:
            return True, 'high'
        elif intent in medium_priority_intents:
            return True, 'medium' if score >= 2 else 'low'
        else:
            return False, 'low'
    
    def _analyze_with_llm(self, text: str) -> Dict:
        """使用 LLM 进行意图识别(兜底方案)"""
        prompt = f"""请分析以下文本中用户的意图:

文本: "{text}"

请从以下类别中选择最匹配的意图:
- 咨询: 询问信息、寻求帮助、了解详情
- 投诉: 表达不满、抱怨问题、要求解决
- 表扬: 表达赞赏、肯定、感谢
- 建议: 提出改进意见、反馈想法
- 退款: 申请退款、退货、取消订单
- 物流: 询问快递、配送、发货相关问题
- 闲聊: 日常对话、寒暄、无明确目的
- 其他: 无法归类的意图

输出严格的 JSON 格式:
{{
  "intent": "咨询/投诉/表扬/建议/退款/物流/闲聊/其他",
  "confidence": 0.90,
  "action_needed": true,
  "priority": "high/medium/low",
  "reason": "简短说明判断理由"
}}

只输出 JSON,不要其他内容。"""

        try:
            response = self.llm.invoke(prompt)
            result = json.loads(response.content.strip())
            return result
        except Exception as e:
            return {
                "intent": "未知",
                "confidence": 0,
                "action_needed": False,
                "priority": "low",
                "error": str(e)
            }
