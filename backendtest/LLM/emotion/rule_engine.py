"""
情感分析后处理规则引擎
基于规则修正词典分析的明显错误
"""
import re
from typing import Dict


class SentimentRuleEngine:
    """情感分析规则引擎"""
    
    def __init__(self):
        # 定义修正规则
        self.rules = [
            self._rule_double_negation,      # 双重否定转正面
            self._rule_rhetorical_question,  # 反问句检测
            self._rule_comparison_structure, # 比较结构检测
            self._rule_irony_detection,      # 简单反语检测
            self._rule_intensity_boost,      # 强度词增强
        ]
    
    def apply_rules(self, text: str, result: Dict) -> Dict:
        """
        应用规则修正情感分析结果
        
        Args:
            text: 原始文本
            result: 词典分析结果
        
        Returns:
            修正后的结果
        """
        original_label = result.get('label', 'neutral')
        original_score = result.get('score', 0)
        
        # 依次应用规则
        for rule in self.rules:
            modified_result = rule(text, result.copy())
            if modified_result:
                result = modified_result
        
        # 记录是否被修正
        if result.get('label') != original_label or abs(result.get('score', 0) - original_score) > 0.1:
            result['corrected'] = True
            result['original_label'] = original_label
            result['original_score'] = original_score
        else:
            result['corrected'] = False
        
        return result
    
    def _rule_double_negation(self, text: str, result: Dict) -> Dict:
        """
        规则1: 双重否定转正面
        
        例如："不是不好" → 应该是正面
        """
        # 检测双重否定模式
        double_neg_patterns = [
            r'不.*不[好坏差烂糟]',  # 不不好、不坏
            r'没.*不[好坏差烂糟]',  # 没不好
            r'并非.*不[好坏差烂糟]',  # 并非不好
        ]
        
        for pattern in double_neg_patterns:
            if re.search(pattern, text):
                # 如果当前是负面，翻转为正面
                if result.get('label') == 'negative':
                    result['label'] = 'positive'
                    result['label_cn'] = '正面'
                    result['score'] = abs(result.get('score', 0)) * 0.8  # 适度正面
                    result['correction_reason'] = '检测到双重否定，翻转为正面'
                    return result
        
        return None
    
    def _rule_rhetorical_question(self, text: str, result: Dict) -> Dict:
        """
        规则2: 反问句情感强化
        
        例如："难道这还不好吗？" → 强烈正面
        """
        rhetorical_patterns = [
            r'难道.*不.*[吗么]?',
            r'怎能.*不.*[呢吗]?',
            r'谁.*不.*[呢吗]?',
        ]
        
        for pattern in rhetorical_patterns:
            if re.search(pattern, text):
                # 反问句通常表达强烈情感
                if result.get('label') == 'positive':
                    result['score'] = min(result.get('score', 0) * 1.3, 1.0)
                    result['correction_reason'] = '反问句，情感强化'
                elif result.get('label') == 'negative':
                    result['score'] = max(result.get('score', 0) * 1.3, -1.0)
                    result['correction_reason'] = '反问句，情感强化'
                return result
        
        return None
    
    def _rule_comparison_structure(self, text: str, result: Dict) -> Dict:
        """
        规则3: 比较结构检测
        
        例如："比之前好多了" → 正面
              "不如以前" → 负面
        """
        # 正面比较
        positive_comp = [
            r'比.*好',
            r'比.*强',
            r'比.*棒',
            r'比.*优秀',
        ]
        
        # 负面比较
        negative_comp = [
            r'比.*差',
            r'比.*烂',
            r'不如',
            r'比不上',
        ]
        
        for pattern in positive_comp:
            if re.search(pattern, text):
                if result.get('label') != 'positive':
                    result['label'] = 'positive'
                    result['label_cn'] = '正面'
                    result['score'] = max(result.get('score', 0), 0.5)
                    result['correction_reason'] = '检测到正面比较结构'
                    return result
        
        for pattern in negative_comp:
            if re.search(pattern, text):
                if result.get('label') != 'negative':
                    result['label'] = 'negative'
                    result['label_cn'] = '负面'
                    result['score'] = min(result.get('score', 0), -0.5)
                    result['correction_reason'] = '检测到负面比较结构'
                    return result
        
        return None
    
    def _rule_irony_detection(self, text: str, result: Dict) -> Dict:
        """
        规则4: 简单反语检测
        
        例如："呵呵，真好" → 可能是负面
        """
        irony_indicators = [
            ('呵呵', 'positive'),  # "呵呵" + 正面词 → 可能是讽刺
            ('哈哈', 'positive'),
            ('行吧', 'positive'),
            ('算了', 'positive'),
        ]
        
        for indicator, target_sentiment in irony_indicators:
            if indicator in text and result.get('label') == target_sentiment:
                # 降低置信度，标记可能为反语
                result['confidence'] = result.get('confidence', 0.8) * 0.6
                result['possible_irony'] = True
                result['correction_reason'] = f'检测到"{indicator}"，可能为反语，降低置信度'
                return result
        
        return None
    
    def _rule_intensity_boost(self, text: str, result: Dict) -> Dict:
        """
        规则5: 强度词增强
        
        例如："真的真的很好" → 超强正面
        """
        # 重复强调
        repeat_patterns = [
            (r'(非常|特别|真的|超级)\s*\1', 1.5),  # 重复程度副词
            (r'[好好棒棒]\s*[好好棒棒]', 1.4),  # 重复形容词
        ]
        
        for pattern, boost_factor in repeat_patterns:
            if re.search(pattern, text):
                current_score = result.get('score', 0)
                result['score'] = max(-1.0, min(1.0, current_score * boost_factor))
                result['correction_reason'] = f'检测到重复强调，强度x{boost_factor}'
                return result
        
        return None


def test_rule_engine():
    """测试规则引擎"""
    print("=" * 70)
    print("情感分析规则引擎测试".center(60))
    print("=" * 70 + "\n")
    
    engine = SentimentRuleEngine()
    
    test_cases = [
        ("双重否定", "这个产品不是不好", {'label': 'negative', 'score': -0.5}),
        ("反问句", "难道这服务还不好吗？", {'label': 'positive', 'score': 0.6}),
        ("比较结构", "比以前好多了", {'label': 'neutral', 'score': 0.0}),
        ("反语检测", "呵呵，真不错", {'label': 'positive', 'score': 0.8}),
        ("强度增强", "真的真的很好", {'label': 'positive', 'score': 0.7}),
    ]
    
    for desc, text, base_result in test_cases:
        print(f"【{desc}】")
        print(f"文本: {text}")
        print(f"修正前: {base_result['label']} (得分: {base_result['score']})")
        
        corrected = engine.apply_rules(text, base_result.copy())
        
        print(f"修正后: {corrected['label']} (得分: {corrected['score']})")
        if corrected.get('corrected'):
            print(f"修正原因: {corrected.get('correction_reason', '未知')}")
        print()


if __name__ == '__main__':
    test_rule_engine()
