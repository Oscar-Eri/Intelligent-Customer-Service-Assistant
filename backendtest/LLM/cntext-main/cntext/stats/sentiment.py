import re
import jieba
import pandas as pd
from nltk.tokenize import word_tokenize, sent_tokenize
from ..stats.utils import STOPWORDS_zh, STOPWORDS_en, zh_split_sentences
from ..io.dict import read_yaml_dict
import logging
import numpy as np
jieba_logger = logging.getLogger('jieba')
jieba_logger.setLevel(logging.CRITICAL)

# 加载程度副词和否定词词典
try:
    ADV_CONJ_DICT = read_yaml_dict(yfile='enzh_common_AdvConj.yaml')['Dictionary']
    NEGATION_WORDS_ZH = ['不', '没', '没有', '别', '非', '未', '莫', '勿', '休', '甭', '无', '否']
    NEGATION_WORDS_EN = ['not', 'no', 'never', 'neither', 'nobody', 'nothing', 'nowhere', 'nor', 
                         "n't", "don't", "doesn't", "didn't", "won't", "wouldn't", "shouldn't", 
                         "couldn't", "isn't", "aren't", "wasn't", "weren't"]
    
    # 程度副词及其权重
    DEGREE_ADVERBS_ZH = {
        '极其': 2.0, '极度': 2.0, '非常': 1.8, '十分': 1.8, '特别': 1.8,
        '很': 1.5, '太': 1.5, '真': 1.5, '挺': 1.3, '相当': 1.3,
        '比较': 1.0, '稍微': 0.7, '略微': 0.7, '有点': 0.5, '稍稍': 0.5
    }
    
    DEGREE_ADVERBS_EN = {
        'extremely': 2.0, 'incredibly': 2.0, 'very': 1.8, 'highly': 1.8,
        'really': 1.5, 'quite': 1.3, 'rather': 1.3, 'fairly': 1.0,
        'somewhat': 0.7, 'slightly': 0.5, 'barely': 0.3
    }
except:
    NEGATION_WORDS_ZH = ['不', '没', '没有', '别', '非', '未']
    NEGATION_WORDS_EN = ['not', 'no', 'never', "n't"]
    DEGREE_ADVERBS_ZH = {'很': 1.5, '非常': 1.8, '特别': 1.8, '太': 1.5}
    DEGREE_ADVERBS_EN = {'very': 1.8, 'extremely': 2.0, 'really': 1.5}


def sentiment_with_context(text, diction, lang='chinese', return_series=False, consider_negation=True, consider_degree=True):
    """
    增强版情感分析，考虑否定词和程度副词的影响。
    
    Args:
        text (str): 待分析的文本字符串
        diction (dict): 情感词典，格式同sentiment函数
        lang (str, optional): 文本语言类型，中文chinese、英文english，默认chinese
        return_series (bool, optional): 是否返回pd.Series类型，默认False
        consider_negation (bool, optional): 是否考虑否定词影响，默认True
        consider_degree (bool, optional): 是否考虑程度副词影响，默认True
    
    Returns:
        dict or pd.Series: 包含各情感类别计数及加权得分
    """
    result_dict = dict()
    senti_categories = list(diction.keys())
    
    # 初始化计数器
    for category in senti_categories:
        result_dict[f'{category}_num'] = 0
        result_dict[f'{category}_score'] = 0.0
    
    stopword_num = 0
    negation_count = 0
    
    if lang == 'chinese':
        # 添加词典词语到jieba
        for category in senti_categories:
            for w in diction[category]:
                try:
                    jieba.add_word(w, freq=20000)
                except:
                    pass
        
        sentence_num = len(zh_split_sentences(text))
        words = list(jieba.cut(text))
        word_num = len(words)
        
        # 遍历词语，考虑上下文
        for i, word in enumerate(words):
            if word in STOPWORDS_zh:
                stopword_num += 1
            
            # 检查是否为情感词
            for category in senti_categories:
                if word in diction[category]:
                    result_dict[f'{category}_num'] += 1
                    
                    # 基础得分为1
                    score = 1.0
                    
                    # 考虑否定词（向前查找1-2个词）
                    if consider_negation:
                        negation_range = range(max(0, i-2), i)
                        for j in negation_range:
                            if words[j] in NEGATION_WORDS_ZH:
                                score *= -1  # 情感反转
                                negation_count += 1
                                break
                    
                    # 考虑程度副词（向前查找1个词）
                    if consider_degree:
                        if i > 0 and words[i-1] in DEGREE_ADVERBS_ZH:
                            score *= DEGREE_ADVERBS_ZH[words[i-1]]
                    
                    result_dict[f'{category}_score'] += score
    
    else:  # English
        sentence_num = len(re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text.lower()))
        rgx = re.compile(r"(?:(?:[^a-zA-Z]+')|(?:'[^a-zA-Z]+))|(?:[^a-zA-Z']+)")
        words = [w.lower() for w in re.split(rgx, text) if w]
        word_num = len(words)
        
        for i, word in enumerate(words):
            if word in STOPWORDS_en:
                stopword_num += 1
            
            for category in senti_categories:
                if word in diction[category]:
                    result_dict[f'{category}_num'] += 1
                    score = 1.0
                    
                    # 考虑否定词
                    if consider_negation:
                        negation_range = range(max(0, i-2), i)
                        for j in negation_range:
                            if words[j] in NEGATION_WORDS_EN or words[j].endswith("n't"):
                                score *= -1
                                negation_count += 1
                                break
                    
                    # 考虑程度副词
                    if consider_degree:
                        if i > 0 and words[i-1] in DEGREE_ADVERBS_EN:
                            score *= DEGREE_ADVERBS_EN[words[i-1]]
                    
                    result_dict[f'{category}_score'] += score
    
    result_dict['stopword_num'] = stopword_num
    result_dict['word_num'] = word_num
    result_dict['sentence_num'] = sentence_num
    result_dict['negation_count'] = negation_count
    
    if return_series:
        return pd.Series(result_dict)
    return result_dict


def sentiment_by_sentence(text, diction, lang='chinese', return_df=False):
    """
    按句子进行情感分析，返回每个句子的情感分布。
    
    Args:
        text (str): 待分析的文本
        diction (dict): 情感词典
        lang (str, optional): 语言类型，默认chinese
        return_df (bool, optional): 是否返回DataFrame，默认False
    
    Returns:
        list or DataFrame: 每个句子的情感分析结果
    """
    if lang == 'chinese':
        sentences = zh_split_sentences(text)
    else:
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        sentences = [s.strip() for s in sentences if s.strip()]
    
    results = []
    for idx, sentence in enumerate(sentences):
        if sentence.strip():
            senti_result = sentiment(sentence, diction, lang=lang)
            senti_result['sentence_id'] = idx
            senti_result['sentence'] = sentence[:50]  # 只保留前50字符
            results.append(senti_result)
    
    if return_df:
        return pd.DataFrame(results)
    return results


def get_sentiment_polarity(result_dict, positive_categories=None, negative_categories=None):
    """
    根据情感分析结果计算整体情感极性。
    
    Args:
        result_dict (dict): sentiment或sentiment_with_context的返回结果
        positive_categories (list, optional): 积极情感类别列表，如['乐', '好']
        negative_categories (list, optional): 消极情感类别列表，如['怒', '哀', '惧', '恶']
    
    Returns:
        dict: 包含极性分数和标签
    """
    if positive_categories is None:
        positive_categories = ['乐', '好', 'joy', 'positive']
    if negative_categories is None:
        negative_categories = ['怒', '哀', '惧', '恶', 'anger', 'sadness', 'fear', 'disgust', 'negative']
    
    positive_score = 0
    negative_score = 0
    
    # 优先使用加权得分，如果没有则使用计数
    use_score = any(f'{cat}_score' in result_dict for cat in positive_categories + negative_categories)
    
    for cat in positive_categories:
        key = f'{cat}_score' if use_score else f'{cat}_num'
        if key in result_dict:
            positive_score += result_dict[key]
    
    for cat in negative_categories:
        key = f'{cat}_score' if use_score else f'{cat}_num'
        if key in result_dict:
            negative_score += result_dict[key]
    
    total = positive_score + negative_score
    if total == 0:
        polarity_score = 0
        polarity_label = 'neutral'
    else:
        polarity_score = (positive_score - negative_score) / total
        if polarity_score > 0.1:
            polarity_label = 'positive'
        elif polarity_score < -0.1:
            polarity_label = 'negative'
        else:
            polarity_label = 'neutral'
    
    return {
        'polarity_score': round(polarity_score, 4),
        'polarity_label': polarity_label,
        'positive_score': positive_score,
        'negative_score': negative_score
    }


def sentiment_advanced(text, diction, lang='chinese', return_series=False, 
                      with_context=True, with_polarity=True,
                      positive_categories=None, negative_categories=None):
    """
    高级情感分析函数，整合多种分析功能。
    
    Args:
        text (str): 待分析文本
        diction (dict): 情感词典
        lang (str, optional): 语言类型，默认chinese
        return_series (bool, optional): 是否返回Series，默认False
        with_context (bool, optional): 是否考虑上下文（否定词、程度副词），默认True
        with_polarity (bool, optional): 是否计算情感极性，默认True
        positive_categories (list, optional): 积极情感类别
        negative_categories (list, optional): 消极情感类别
    
    Returns:
        dict or pd.Series: 综合情感分析结果
    """
    # 基础情感分析
    if with_context:
        result = sentiment_with_context(text, diction, lang=lang, return_series=False)
    else:
        result = sentiment(text, diction, lang=lang, return_series=False)
    
    # 计算情感极性
    if with_polarity:
        polarity_info = get_sentiment_polarity(
            result, 
            positive_categories=positive_categories,
            negative_categories=negative_categories
        )
        result.update(polarity_info)
    
    if return_series:
        return pd.Series(result)
    return result


    


def sentiment_by_valence(text, diction, lang='chinese', mean=False, return_series=False):
    """
    Calculate the occurrences of each sentiment category words in text;
    the complex influence of intensity adverbs and negative words on emotion is not considered.
    
    Args:
        text (str): 待分析的文本字符串
        diction (dict): 格式为Python字典类型
        lang (str, optional):文本的语言类型， 中文chinese、英文english，默认chinese。
        mean (boolean, optional): 是否基于词语数量统计情绪信息， 默认False. 
        return_series(boolean, optional): 计算结果是否输出为pd.Series类型，默认为False

    Returns:
        dict(or pd.Series)
    """

    result = dict()
    attrs = pd.DataFrame(diction).index
    for attr in attrs:
        result[attr] = 0
    

    if lang == 'chinese':
        words = list(jieba.cut(text))
        for word in words:
            if diction.get(word):
                for attr in attrs:
                    result[attr] = result[attr] + diction.get(word)[attr]


    else:
        text = text.lower()
        #rgx = re.compile("(?:(?:[^a-zA-Z]+')|(?:'[^a-zA-Z]+))|(?:[^a-zA-Z']+)")
        #words = re.split(rgx, text)
        try:
            words = word_tokenize(text)
        except:
            #print('你的电脑nltk没配置好，请观看视频https://www.bilibili.com/video/BV14A411i7DB')
            rgx = re.compile(r"(?:(?:[^a-zA-Z]+')|(?:'[^a-zA-Z]+))|(?:[^a-zA-Z']+)")
            words = re.split(rgx, text)

        for word in words:
            if diction.get(word):
                for attr in attrs:
                    result[attr] = result[attr] + diction.get(word)[attr]
      
    result['word_num'] = len(words)
    
    if mean==True:
        for attr in attrs:
            result[attr] = round(result[attr]/len(words), 3)
    if return_series:
        return pd.Series(result)
    return result 