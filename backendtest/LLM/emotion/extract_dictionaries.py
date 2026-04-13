"""
增强版cntext词典提取工具
提取所有可用的中文词典数据，支持多种应用场景
"""
import yaml
import json
import os
from pathlib import Path


class DictionaryExtractor:
    """cntext词典提取器"""
    
    def __init__(self, cntext_data_dir=None):
        """
        初始化提取器
        
        Args:
            cntext_data_dir: cntext词典数据目录路径
        """
        if cntext_data_dir is None:
            # 默认路径
            self.data_dir = r'E:\QRTlongchaintraining\PROJ\AIchattest\backendtest\LLM\cntext-main\cntext\io\data'
        else:
            self.data_dir = cntext_data_dir
        
        # 输出目录
        self.output_dir = os.path.join(os.path.dirname(__file__), 'dictionaries')
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"📂 数据目录: {self.data_dir}")
        print(f"📁 输出目录: {self.output_dir}\n")
    
    def extract_all_chinese_dictionaries(self):
        """提取所有中文词典"""
        print("=" * 70)
        print("开始提取所有中文词典".center(60))
        print("=" * 70 + "\n")
        
        # 定义要提取的词典配置
        dict_configs = [
            {
                'name': 'DUTIR情感本体库',
                'file': 'zh_common_DUTIR.yaml',
                'type': 'sentiment_7categories',
                'description': '大连理工大学7类情感词典（乐、好、怒、哀、惧、恶、惊）'
            },
            {
                'name': 'NTUSD情感词典',
                'file': 'zh_common_NTUSD.yaml',
                'type': 'sentiment_binary',
                'description': '台湾大学正负面情感词典'
            },
            {
                'name': 'HowNet情感词典',
                'file': 'zh_common_HowNet.yaml',
                'type': 'sentiment_hownet',
                'description': '知网情感词典'
            },
            {
                'name': '六维度语义数据库',
                'file': 'zh_valence_SixSemanticDimensionDatabase.yaml',
                'type': 'semantic_dimensions',
                'description': '17,940个词的6维语义评分（视觉、社交、情感、时间、空间、动作）'
            },
            {
                'name': '程度副词与连词',
                'file': 'enzh_common_AdvConj.yaml',
                'type': 'adverbs_conjunctions',
                'description': '中英文程度副词和连词（用于情感加权）'
            },
            {
                'name': '停用词表',
                'file': 'enzh_common_StopWords.yaml',
                'type': 'stopwords',
                'description': '中英文停用词表'
            },
            {
                'name': '清华褒贬词典',
                'file': 'zh_common_TsinghuaPraiseDegrade.yaml',
                'type': 'praise_degrade',
                'description': '清华大学褒义词和贬义词词典'
            },
            {
                'name': '金融情感词典',
                'file': 'zh_common_FinanceSenti.yaml',
                'type': 'finance_sentiment',
                'description': '金融领域专用情感词典'
            },
            {
                'name': '数字化词典',
                'file': 'zh_common_Digitalization.yaml',
                'type': 'digitalization',
                'description': '数字化转型相关词汇'
            },
            {
                'name': '经济政策不确定性',
                'file': 'zh_common_EPU.yaml',
                'type': 'epu',
                'description': '经济政策不确定性关键词'
            },
            {
                'name': '企业不确定性感知',
                'file': 'zh_common_FEPU.yaml',
                'type': 'fepu',
                'description': '企业层面不确定性感知词汇'
            }
        ]
        
        results = {}
        
        for config in dict_configs:
            try:
                result = self._extract_single_dictionary(config)
                if result:
                    results[config['name']] = result
            except Exception as e:
                print(f"❌ 提取失败 [{config['name']}]: {e}\n")
        
        # 保存汇总信息
        summary_path = os.path.join(self.output_dir, 'extraction_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_dicts': len(results),
                'dictionaries': list(results.keys()),
                'extraction_time': str(Path(self.data_dir).stat().st_mtime)
            }, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 70)
        print(f"✅ 提取完成！共成功提取 {len(results)} 个词典")
        print("=" * 70)
        
        return results
    
    def _extract_single_dictionary(self, config):
        """提取单个词典"""
        file_path = os.path.join(self.data_dir, config['file'])
        
        if not os.path.exists(file_path):
            print(f"⚠️  文件不存在: {config['file']}")
            return None
        
        print(f"📖 正在提取: {config['name']}")
        print(f"   文件: {config['file']}")
        print(f"   说明: {config['description']}")
        
        # 读取YAML文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        dictionary = data.get('Dictionary', {})
        
        # 根据类型处理
        if config['type'] == 'sentiment_7categories':
            result = self._process_dutir(dictionary, config)
        elif config['type'] == 'sentiment_binary':
            result = self._process_ntusd(dictionary, config)
        elif config['type'] == 'semantic_dimensions':
            result = self._process_six_dimensions(dictionary, config)
        elif config['type'] == 'adverbs_conjunctions':
            result = self._process_adverbs_conjunctions(dictionary, config)
        elif config['type'] == 'stopwords':
            result = self._process_stopwords(dictionary, config)
        elif config['type'] == 'praise_degrade':
            result = self._process_praise_degrade(dictionary, config)
        else:
            # 通用处理：直接保存
            result = self._save_generic_dict(dictionary, config)
        
        if result:
            print(f"   ✅ 成功提取 {result.get('total_words', 0)} 个词汇\n")
        
        return result
    
    def _process_dutir(self, dictionary, config):
        """处理DUTIR情感词典（7类情感）"""
        categories = ['乐', '好', '怒', '哀', '惧', '恶', '惊']
        
        # 按类别提取
        result = {
            'categories': {},
            'metadata': {
                'source': config['name'],
                'description': config['description'],
                'categories': categories
            }
        }
        
        total_words = 0
        for cat in categories:
            words = dictionary.get(cat, [])
            result['categories'][cat] = words
            total_words += len(words)
            print(f"      - {cat}: {len(words)} 词")
        
        # 同时生成简化版（正面/负面）
        positive = dictionary.get('乐', []) + dictionary.get('好', [])
        negative = (
            dictionary.get('哀', []) + 
            dictionary.get('怒', []) + 
            dictionary.get('恶', []) + 
            dictionary.get('惧', [])
        )
        
        result['simplified'] = {
            'positive': positive,
            'negative': negative
        }
        result['metadata']['positive_count'] = len(positive)
        result['metadata']['negative_count'] = len(negative)
        result['total_words'] = total_words
        
        # 保存
        output_path = os.path.join(self.output_dir, 'dutir_sentiment.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    
    def _process_ntusd(self, dictionary, config):
        """处理NTUSD情感词典（正/负）"""
        positive = dictionary.get('positive', [])
        negative = dictionary.get('negative', [])
        
        result = {
            'positive': positive,
            'negative': negative,
            'metadata': {
                'source': config['name'],
                'description': config['description'],
                'positive_count': len(positive),
                'negative_count': len(negative)
            },
            'total_words': len(positive) + len(negative)
        }
        
        # 保存
        output_path = os.path.join(self.output_dir, 'ntusd_sentiment.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    
    def _process_six_dimensions(self, dictionary, config):
        """处理六维度语义数据库"""
        # 这个词典很大，只保存元数据和示例
        dimensions = ['vision', 'socialness', 'emotion', 'time', 'space', 'motor']
        
        # 统计信息
        total_words = len(dictionary)
        
        # 提取示例（前100个词）
        sample = {}
        for i, (word, scores) in enumerate(dictionary.items()):
            if i >= 100:
                break
            sample[word] = scores
        
        result = {
            'metadata': {
                'source': config['name'],
                'description': config['description'],
                'dimensions': dimensions,
                'total_words': total_words,
                'note': '完整数据太大，仅保存元数据和示例。如需完整数据请单独提取。'
            },
            'sample_data': sample
        }
        
        # 保存元数据
        output_path = os.path.join(self.output_dir, 'six_dimensions_metadata.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    
    def _process_adverbs_conjunctions(self, dictionary, config):
        """处理程度副词和连词"""
        zh_adv = dictionary.get('zh_adv', [])
        zh_conj = dictionary.get('zh_conj', [])
        
        result = {
            'zh_adverbs': zh_adv,
            'zh_conjunctions': zh_conj,
            'metadata': {
                'source': config['name'],
                'description': config['description'],
                'adverbs_count': len(zh_adv),
                'conjunctions_count': len(zh_conj)
            },
            'total_words': len(zh_adv) + len(zh_conj)
        }
        
        # 保存
        output_path = os.path.join(self.output_dir, 'adverbs_conjunctions.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    
    def _process_stopwords(self, dictionary, config):
        """处理停用词表"""
        zh_stopwords = dictionary.get('chinese', [])
        en_stopwords = dictionary.get('english', [])
        
        result = {
            'chinese': zh_stopwords,
            'english': en_stopwords,
            'metadata': {
                'source': config['name'],
                'description': config['description'],
                'chinese_count': len(zh_stopwords),
                'english_count': len(en_stopwords)
            },
            'total_words': len(zh_stopwords) + len(en_stopwords)
        }
        
        # 保存
        output_path = os.path.join(self.output_dir, 'stopwords.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    
    def _process_praise_degrade(self, dictionary, config):
        """处理清华褒贬词典"""
        praise = dictionary.get('praise', [])
        degrade = dictionary.get('degrade', [])
        
        result = {
            'praise': praise,
            'degrade': degrade,
            'metadata': {
                'source': config['name'],
                'description': config['description'],
                'praise_count': len(praise),
                'degrade_count': len(degrade)
            },
            'total_words': len(praise) + len(degrade)
        }
        
        # 保存
        output_path = os.path.join(self.output_dir, 'tsinghua_praise_degrade.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    
    def _save_generic_dict(self, dictionary, config):
        """通用词典保存"""
        # 统计各类别
        stats = {}
        total = 0
        for key, value in dictionary.items():
            if isinstance(value, list):
                stats[key] = len(value)
                total += len(value)
        
        result = {
            'dictionary': dictionary,
            'metadata': {
                'source': config['name'],
                'description': config['description'],
                'categories_stats': stats
            },
            'total_words': total
        }
        
        # 保存
        safe_name = config['name'].replace(' ', '_').replace('/', '_')
        output_path = os.path.join(self.output_dir, f'{safe_name}.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result


def main():
    """主函数"""
    extractor = DictionaryExtractor()
    
    # 提取所有词典
    results = extractor.extract_all_chinese_dictionaries()
    
    # 打印总结
    print("\n" + "=" * 70)
    print("词典提取总结".center(60))
    print("=" * 70)
    
    for name, data in results.items():
        total = data.get('total_words', 0)
        print(f"✓ {name}: {total:,} 词")
    
    print("\n💡 提示:")
    print("   - 所有词典已保存到 dictionaries/ 目录")
    print("   - 可以在 sentiment_analyzer.py 和 intent_analyzer.py 中使用")
    print("   - 建议定期更新以保持词典时效性")


if __name__ == '__main__':
    main()
