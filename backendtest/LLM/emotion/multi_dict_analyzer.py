"""
多词典融合情感分析器
使用DUTIR + NTUSD + HowNet三个词典投票机制，提高准确率
"""
import os
import json
from typing import Dict, List
from collections import Counter
import jieba


class MultiDictSentimentAnalyzer:
    """多词典融合情感分析器"""
    
    def __init__(self):
        self.dictionaries = {}
        self._load_all_dictionaries()
    
    def _load_all_dictionaries(self):
        """加载所有情感词典"""
        dict_dir = os.path.join(os.path.dirname(__file__), 'dictionaries')
        
        # 1. 加载DUTIR词典
        try:
            with open(os.path.join(dict_dir, 'dutir_sentiment.json'), 'r', encoding='utf-8') as f:
                dutir_data = json.load(f)
                self.dictionaries['DUTIR'] = {
                    'positive': set(dutir_data['simplified']['positive']),
                    'negative': set(dutir_data['simplified']['negative'])
                }
                print(f"✅ DUTIR词典已加载: 正面{len(self.dictionaries['DUTIR']['positive'])}词, "
                      f"负面{len(self.dictionaries['DUTIR']['negative'])}词")
        except Exception as e:
            print(f"⚠️  DUTIR词典加载失败: {e}")
        
        # 2. 加载NTUSD词典
        try:
            with open(os.path.join(dict_dir, 'ntusd_sentiment.json'), 'r', encoding='utf-8') as f:
                ntusd_data = json.load(f)
                self.dictionaries['NTUSD'] = {
                    'positive': set(ntusd_data['positive']),
                    'negative': set(ntusd_data['negative'])
                }
                print(f"✅ NTUSD词典已加载: 正面{len(self.dictionaries['NTUSD']['positive'])}词, "
                      f"负面{len(self.dictionaries['NTUSD']['negative'])}词")
        except Exception as e:
            print(f"⚠️  NTUSD词典加载失败: {e}")
        
        # 3. 加载HowNet词典
        try:
            with open(os.path.join(dict_dir, 'HowNet情感词典.json'), 'r', encoding='utf-8') as f:
                hownet_data = json.load(f)
                self.dictionaries['HowNet'] = {
                    'positive': set(hownet_data.get('positive', [])),
                    'negative': set(hownet_data.get('negative', []))
                }
                print(f"✅ HowNet词典已加载: 正面{len(self.dictionaries['HowNet']['positive'])}词, "
                      f"负面{len(self.dictionaries['HowNet']['negative'])}词")
        except Exception as e:
            print(f"⚠️  HowNet词典加载失败: {e}")
        
        # 4. 加载清华褒贬词典
        try:
            with open(os.path.join(dict_dir, 'tsinghua_praise_degrade.json'), 'r', encoding='utf-8') as f:
                tsinghua_data = json.load(f)
                self.dictionaries['Tsinghua'] = {
                    'positive': set(tsinghua_data.get('praise', [])),
                    'negative': set(tsinghua_data.get('degrade', []))
                }
                print(f"✅ 清华褒贬词典已加载: 褒义{len(self.dictionaries['Tsinghua']['positive'])}词, "
                      f"贬义{len(self.dictionaries['Tsinghua']['negative'])}词")
        except Exception as e:
            print(f"⚠️  清华褒贬词典加载失败: {e}")
        
        print(f"\n📊 共加载 {len(self.dictionaries)} 个情感词典\n")
    
    def analyze(self, text: str, use_voting: bool = True) -> Dict:
        """
        执行情感分析
        
        Args:
            text: 待分析文本
            use_voting: 是否使用投票机制
        
        Returns:
            {
                "label": "positive/negative/neutral",
                "label_cn": "正面/负面/中性",
                "score": 0.85,
                "confidence": 0.9,
                "voting_details": {...},  # 投票详情
                "matched_words": {...}
            }
        """
        if use_voting and len(self.dictionaries) > 1:
            return self._analyze_with_voting(text)
        else:
            # 降级为单词典分析（使用DUTIR）
            return self._analyze_single_dict(text, 'DUTIR')
    
    def _analyze_with_voting(self, text: str) -> Dict:
        """使用多词典投票机制"""
        # 分词
        words = list(jieba.cut(text))
        
        # 每个词典独立分析
        voting_results = {}
        all_matched_words = {'positive': set(), 'negative': set()}
        
        for dict_name, dictionary in self.dictionaries.items():
            result = self._analyze_single_dict_with_words(text, words, dictionary)
            voting_results[dict_name] = result
            
            # 收集所有匹配的词
            all_matched_words['positive'].update(result.get('matched_positive', []))
            all_matched_words['negative'].update(result.get('matched_negative', []))
        
        # 投票统计
        votes = Counter()
        scores = []
        
        for dict_name, result in voting_results.items():
            label = result['label']
            votes[label] += 1
            scores.append(result['score'])
        
        # 得票最多的标签
        best_label = votes.most_common(1)[0][0]
        
        # 平均得分
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 置信度计算：基于一致性和匹配词数量
        total_matches = len(all_matched_words['positive']) + len(all_matched_words['negative'])
        agreement_ratio = votes.most_common(1)[0][1] / len(self.dictionaries)  # 一致性比例
        
        confidence = min(agreement_ratio * 0.7 + (total_matches / 10) * 0.3, 1.0)
        
        # 映射标签
        label_map = {
            'positive': ('positive', '正面'),
            'negative': ('negative', '负面'),
            'neutral': ('neutral', '中性')
        }
        label_en, label_cn = label_map.get(best_label, ('neutral', '中性'))
        
        return {
            'method': 'multi_dict_voting',
            'label': label_en,
            'label_cn': label_cn,
            'score': round(avg_score, 2),
            'confidence': round(confidence, 2),
            'voting_details': {
                'votes': dict(votes),
                'agreement_ratio': round(agreement_ratio, 2),
                'dict_results': {k: v['label_cn'] for k, v in voting_results.items()}
            },
            'matched_words': {
                'positive': list(all_matched_words['positive']),
                'negative': list(all_matched_words['negative'])
            },
            'reason': f'{len(self.dictionaries)}个词典投票，{votes.most_common(1)[0][1]}票{label_cn}'
        }
    
    def _analyze_single_dict(self, text: str, dict_name: str = 'DUTIR') -> Dict:
        """单词典分析（降级方案）"""
        if dict_name not in self.dictionaries:
            return {'error': f'词典 {dict_name} 未加载'}
        
        words = list(jieba.cut(text))
        dictionary = self.dictionaries[dict_name]
        
        return self._analyze_single_dict_with_words(text, words, dictionary)
    
    def _analyze_single_dict_with_words(self, text: str, words: List[str], dictionary: Dict) -> Dict:
        """使用指定词典分析（传入已分词结果）"""
        pos_matches = [w for w in words if w in dictionary['positive']]
        neg_matches = [w for w in words if w in dictionary['negative']]
        
        pos_count = len(pos_matches)
        neg_count = len(neg_matches)
        total = pos_count + neg_count
        
        if total == 0:
            return {
                'label': 'neutral',
                'label_cn': '中性',
                'score': 0.0,
                'matched_positive': [],
                'matched_negative': []
            }
        
        score = (pos_count - neg_count) / total
        
        if score > 0.2:
            label = 'positive'
            label_cn = '正面'
        elif score < -0.2:
            label = 'negative'
            label_cn = '负面'
        else:
            label = 'neutral'
            label_cn = '中性'
        
        return {
            'label': label,
            'label_cn': label_cn,
            'score': round(score, 2),
            'matched_positive': pos_matches,
            'matched_negative': neg_matches
        }


def test_multi_dict_analyzer():
    """测试多词典融合分析器"""
    print("=" * 70)
    print("多词典融合情感分析器测试".center(60))
    print("=" * 70 + "\n")
    
    analyzer = MultiDictSentimentAnalyzer()
    
    test_cases = [
        "这个产品非常好用，我非常满意！",
        "服务态度太差了，我要投诉！",
        "产品质量一般，价格有点贵",
        "快递很快，包装也很好，感谢",
        "不好也不坏，就那样吧"
    ]
    
    for text in test_cases:
        print(f"文本: {text}")
        
        # 多词典投票
        result = analyzer.analyze(text, use_voting=True)
        print(f"  结果: {result['emoji'] if 'emoji' in result else ''} {result['label_cn']}")
        print(f"  得分: {result['score']}")
        print(f"  置信度: {result['confidence']}")
        print(f"  投票详情: {result['voting_details']['dict_results']}")
        print(f"  匹配词: 正面{result['matched_words']['positive']}, "
              f"负面{result['matched_words']['negative']}")
        print()


if __name__ == '__main__':
    test_multi_dict_analyzer()
