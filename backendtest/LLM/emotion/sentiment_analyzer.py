"""
情感倾向分析模块 (Sentiment Analysis)
独立实现：基于cntext算法逻辑 + 本地词典数据
核心特性：
- 否定词处理（不、没、别等）
- 程度副词加权（非常、很、稍微等）
- 多词典融合投票（DUTIR+NTUSD+HowNet+清华）
- 规则引擎后处理
- LLM兜底机制
"""
import os
import json
import re
from typing import Dict, List
from langchain_openai import ChatOpenAI
import jieba

# 支持直接运行和模块导入两种方式
try:
    from ...config import qwen_base_url, qwen_api_key
except ImportError:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from config import qwen_base_url, qwen_api_key

# 导入多词典分析器和规则引擎
try:
    from .multi_dict_analyzer import MultiDictSentimentAnalyzer
    from .rule_engine import SentimentRuleEngine
    MULTI_DICT_AVAILABLE = True
    RULE_ENGINE_AVAILABLE = True
except ImportError:
    MULTI_DICT_AVAILABLE = False
    RULE_ENGINE_AVAILABLE = False
    print("⚠️  多词典分析器或规则引擎未加载")


class SentimentAnalyzer:
    """独立实现的情感分析器（基于cntext算法）"""
    
    # 否定词列表
    NEGATION_WORDS = ['不', '没', '没有', '别', '非', '未', '莫', '勿', '休', '甭', '无', '否']
    
    # 程度副词及其权重
    DEGREE_ADVERBS = {
        '极其': 2.0, '极度': 2.0, '最为': 2.0,
        '非常': 1.8, '十分': 1.8, '特别': 1.8, '格外': 1.8,
        '很': 1.5, '太': 1.5, '真': 1.5, '颇': 1.5,
        '挺': 1.3, '相当': 1.3, '较为': 1.3,
        '比较': 1.0,
        '稍微': 0.7, '略微': 0.7, '稍稍': 0.7, '有点': 0.5, '有些': 0.5
    }
    
    def __init__(self, use_multi_dict: bool = True, use_rules: bool = True):
        """
        初始化情感分析器
        
        Args:
            use_multi_dict: 是否使用多词典投票（默认True）
            use_rules: 是否使用规则引擎（默认True）
        """
        # 加载本地词典数据
        self.dict_loaded = self._load_dictionaries()
        
        # 初始化多词典分析器
        self.use_multi_dict = use_multi_dict and MULTI_DICT_AVAILABLE
        if self.use_multi_dict:
            self.multi_dict_analyzer = MultiDictSentimentAnalyzer()
        
        # 初始化规则引擎
        self.use_rules = use_rules and RULE_ENGINE_AVAILABLE
        if self.use_rules:
            self.rule_engine = SentimentRuleEngine()
        
        # 初始化 LLM（仅作为兜底）
        self.llm = ChatOpenAI(
            model="qwen-plus",
            base_url=qwen_base_url,
            api_key=qwen_api_key,
            temperature=0,
            max_tokens=200,
        )
    
    def _load_dictionaries(self) -> bool:
        """加载本地情感词典数据"""
        try:
            dict_path = os.path.join(
                os.path.dirname(__file__),
                'dictionaries',
                'dutir_sentiment.json'
            )
            
            with open(dict_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.sentiment_dict = {
                'positive': set(data['positive']),  # 使用set加速查找
                'negative': set(data['negative'])
            }
            
            print(f"✅ 情感词典已加载: 正面{len(self.sentiment_dict['positive'])}词, 负面{len(self.sentiment_dict['negative'])}词")
            return True
            
        except Exception as e:
            print(f"⚠️  词典加载失败: {e}")
            return False
    
    def analyze(self, text: str, force_llm: bool = False, use_context: bool = True, 
                use_multi_dict: bool = None, use_rules: bool = None) -> Dict:
        """
        执行情感分析（增强版）
        
        Args:
            text: 待分析文本
            force_llm: 是否强制使用 LLM（跳过词典）
            use_context: 是否考虑上下文（否定词、程度副词），默认True
            use_multi_dict: 是否使用多词典投票（默认使用实例配置）
            use_rules: 是否使用规则引擎（默认使用实例配置）
        
        Returns:
            {
                "label": "positive/negative/neutral",
                "label_cn": "正面/负面/中性",
                "score": 0.85,
                "emoji": "😊",
                "method": "multi_dict_voting/dict_with_context/dict_basic/llm",
                "confidence": 0.9
            }
        """
        # 确定是否使用多词典和规则引擎
        use_multi = use_multi_dict if use_multi_dict is not None else self.use_multi_dict
        use_rule = use_rules if use_rules is not None else self.use_rules
        
        # 策略1：多词典投票（最优先）
        if not force_llm and use_multi and MULTI_DICT_AVAILABLE:
            result = self.multi_dict_analyzer.analyze(text, use_voting=True)
            
            # 应用规则引擎修正
            if use_rule and RULE_ENGINE_AVAILABLE:
                result = self.rule_engine.apply_rules(text, result)
            
            # 如果置信度高，直接返回
            if result.get('confidence', 0) >= 0.6:
                result['method'] = 'multi_dict_voting'
                return result
        
        # 策略2：单词典分析（带上下文）
        if not force_llm and self.dict_loaded:
            if use_context:
                dict_result = self._analyze_with_context(text)
            else:
                dict_result = self._analyze_basic(text)
            
            # 应用规则引擎
            if use_rule and RULE_ENGINE_AVAILABLE:
                dict_result = self.rule_engine.apply_rules(text, dict_result)
            
            # 如果词典分析置信度高（>=0.6），直接返回
            if dict_result.get('confidence', 0) >= 0.6:
                return dict_result
        
        # 策略3：LLM 兜底
        return self._analyze_with_llm(text)
    
    def _analyze_basic(self, text: str) -> Dict:
        """基础词典分析（不考虑上下文）"""
        try:
            # 分词
            words = list(jieba.cut(text))
            
            # 统计匹配的情感词
            pos_matches = [w for w in words if w in self.sentiment_dict['positive']]
            neg_matches = [w for w in words if w in self.sentiment_dict['negative']]
            
            pos_count = len(pos_matches)
            neg_count = len(neg_matches)
            total = pos_count + neg_count
            
            # 如果没有匹配到情感词
            if total == 0:
                return {
                    'method': 'dict_basic',
                    'label': 'neutral',
                    'label_cn': '中性',
                    'score': 0.0,
                    'confidence': 0.0,
                    'emoji': '😐',
                    'reason': '未匹配到情感词'
                }
            
            # 计算情感得分
            score = (pos_count - neg_count) / total
            
            # 判断情感倾向
            label, label_cn = self._get_label(score)
            
            # 置信度
            confidence = self._get_confidence(total)
            
            return {
                'method': 'dict_basic',
                'label': label,
                'label_cn': label_cn,
                'score': round(score, 2),
                'confidence': confidence,
                'matched_words': {
                    'positive': pos_matches,
                    'negative': neg_matches
                },
                'emoji': self._get_emoji(label),
                'reason': f'匹配到{total}个情感词（正面{pos_count}，负面{neg_count}）'
            }
            
        except Exception as e:
            print(f"⚠️  基础分析失败: {e}")
            return {'confidence': 0.0}
    
    def _analyze_with_context(self, text: str) -> Dict:
        """
        增强版词典分析（考虑否定词和程度副词）
        核心算法来自cntext的sentiment_with_context
        """
        try:
            # 分词
            words = list(jieba.cut(text))
            
            pos_score = 0.0
            neg_score = 0.0
            pos_matches = []
            neg_matches = []
            negation_count = 0
            
            # 遍历每个词，检查上下文
            for i, word in enumerate(words):
                # 检查是否为情感词
                if word in self.sentiment_dict['positive']:
                    pos_matches.append(word)
                    score = 1.0
                    
                    # 检查否定词（向前查找1-2个词）
                    if self._check_negation(words, i):
                        score *= -1
                        negation_count += 1
                    
                    # 检查程度副词（向前查找1个词）
                    degree_weight = self._check_degree_adverb(words, i)
                    score *= degree_weight
                    
                    pos_score += score
                    
                elif word in self.sentiment_dict['negative']:
                    neg_matches.append(word)
                    score = 1.0
                    
                    # 检查否定词
                    if self._check_negation(words, i):
                        score *= -1
                        negation_count += 1
                    
                    # 检查程度副词
                    degree_weight = self._check_degree_adverb(words, i)
                    score *= degree_weight
                    
                    neg_score += score
            
            total_count = len(pos_matches) + len(neg_matches)
            
            # 如果没有匹配到情感词
            if total_count == 0:
                return {
                    'method': 'dict_with_context',
                    'label': 'neutral',
                    'label_cn': '中性',
                    'score': 0.0,
                    'confidence': 0.0,
                    'emoji': '😐',
                    'reason': '未匹配到情感词'
                }
            
            # 计算最终得分（考虑否定反转后的加权得分）
            final_score = (pos_score - neg_score) / (abs(pos_score) + abs(neg_score) + 0.001)
            final_score = max(-1.0, min(1.0, final_score))  # 限制在[-1, 1]
            
            # 判断情感倾向
            label, label_cn = self._get_label(final_score)
            
            # 置信度（考虑匹配词数量和否定词）
            confidence = self._get_confidence(total_count)
            if negation_count > 0:
                confidence = min(confidence + 0.05, 1.0)  # 有否定词处理，略微提高置信度
            
            return {
                'method': 'dict_with_context',
                'label': label,
                'label_cn': label_cn,
                'score': round(final_score, 2),
                'confidence': confidence,
                'matched_words': {
                    'positive': pos_matches,
                    'negative': neg_matches
                },
                'weighted_scores': {
                    'positive': round(pos_score, 2),
                    'negative': round(neg_score, 2)
                },
                'negation_count': negation_count,
                'emoji': self._get_emoji(label),
                'reason': f'加权分析：正面{pos_score:.2f}，负面{neg_score:.2f}，否定词{negation_count}个'
            }
            
        except Exception as e:
            print(f"⚠️  上下文分析失败: {e}")
            return {'confidence': 0.0}
    
    def _check_negation(self, words: List[str], current_idx: int, window: int = 2) -> bool:
        """检查当前词前面是否有否定词"""
        start = max(0, current_idx - window)
        for i in range(start, current_idx):
            if words[i] in self.NEGATION_WORDS:
                return True
        return False
    
    def _check_degree_adverb(self, words: List[str], current_idx: int) -> float:
        """检查当前词前面是否有程度副词，返回权重"""
        if current_idx > 0:
            prev_word = words[current_idx - 1]
            return self.DEGREE_ADVERBS.get(prev_word, 1.0)
        return 1.0
    
    def _get_label(self, score: float) -> tuple:
        """根据得分判断情感标签"""
        if score > 0.2:
            return 'positive', '正面'
        elif score < -0.2:
            return 'negative', '负面'
        else:
            return 'neutral', '中性'
    
    def _get_confidence(self, word_count: int) -> float:
        """根据匹配词数量计算置信度"""
        if word_count >= 4:
            return 0.95
        elif word_count >= 3:
            return 0.9
        elif word_count >= 2:
            return 0.8
        else:
            return 0.6
    
    def _get_emoji(self, label: str) -> str:
        """获取对应的情感表情"""
        emoji_map = {
            'positive': '😊',
            'negative': '😔',
            'neutral': '😐'
        }
        return emoji_map.get(label, '😐')
    
    def _analyze_with_llm(self, text: str) -> Dict:
        """使用 LLM 进行情感分析（兜底方案）"""
        prompt = f"""请分析以下文本的情感倾向:

文本: "{text}"

请从以下三个类别中选择:
- positive (正面): 表达满意、赞赏、开心等积极情绪
- negative (负面): 表达不满、抱怨、生气等消极情绪  
- neutral (中性): 客观陈述,无明显情感色彩

输出严格的 JSON 格式:
{{
  "label": "positive/negative/neutral",
  "label_cn": "正面/负面/中性",
  "score": 0.85,
  "reason": "简短说明判断理由"
}}

其中 score 范围是 -1 到 1。只输出 JSON,不要其他内容。"""

        try:
            response = self.llm.invoke(prompt)
            import json
            result = json.loads(response.content.strip())
            
            emoji_map = {
                "positive": "😊",
                "negative": "😔",
                "neutral": "😐"
            }
            result["emoji"] = emoji_map.get(result["label"], "😐")
            result["method"] = "llm"
            result["confidence"] = 0.9
            return result
        except Exception as e:
            return {
                "label": "unknown",
                "label_cn": "未知",
                "score": 0,
                "emoji": "❓",
                "method": "llm",
                "confidence": 0.0,
                "error": str(e)
            }
