import numpy as np
import scipy.spatial.distance
import itertools
from .model.utils import preprocess_line
from .io.utils import clean_text
from functools import lru_cache



def project_word(wv, a, b, cosine=False):
    """
    在向量空间中， 计算词语a在词语b上的投影值。

    Args:
        wv (KeyedVectors): 语言模型的KeyedVectors
        a : 词语a字符串或列表
        b:  词语字符串、词语列表、或某概念向量
        cosine (bool, optional): 投影值是否使用余弦相似度， 默认为False，返回a在b上的投影值； True时，返回a与b的余弦相似度。

    Returns:
        float: 词语a在词语b上的投影值。
    """

    # 计算向量 A 和向量 B
    if isinstance(a, str):
        vec_a = wv[a]
    else:
        vec_a = wv.get_mean_vector(a)

    if isinstance(b, np.ndarray):
        vec_b = b
    elif isinstance(b, str):
        vec_b = wv[b]
    else:
        vec_b = wv.get_mean_vector(b)
    if cosine:
        return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
    else:
        return np.dot(vec_a, vec_b) / np.linalg.norm(vec_b)
    
    
def project_text(wv, text, axis, lang='chinese', cosine=False):
    """
    在向量空间中，计算文本在概念轴向量上的投影值。
    
    Args:
        wv(KeyedVectors): 语言模型的KeyedVectors
        text : 文本字符串
        lang:  语言,有chinese和english两种; 默认"chinese"
        axis:  概念向量
        cosine (bool, optional): 投影值是否使用余弦相似度， 默认为False，返回text在axis上的投影值； True时，返回text与axis的余弦相似度。

    Returns:
        float: 文本在概念轴上的投影值。如果无法计算，则返回 np.nan。
    """
    # 1. 检查概念轴向量的有效性
    if isinstance(axis, np.ndarray):
        vec_axis = axis
    elif isinstance(axis, list) or isinstance(axis, tuple):
        try:
            vec_axis = wv.get_mean_vector(axis)
        except KeyError:
            # If the list is empty or words don't exist, get_mean_vector might raise an error
            return np.nan
    else:
        # Invalid axis type
        return np.nan

    # 2. 检查概念轴向量是否为零向量
    if np.linalg.norm(vec_axis) == 0:
        return np.nan
    

    # 3. 处理文本并获取有效词汇
    words = preprocess_line(line=text,lang=lang)
    valid_words = [w for w in words if w in wv]
    
    if not valid_words:
        return np.nan

    # 4. 计算投影
    result = 0
    for w in valid_words:
        vec_w = wv[w]
        
        if cosine:
            res = np.dot(vec_w, vec_axis) / (np.linalg.norm(vec_w) * np.linalg.norm(vec_axis))
        else:
            res = np.dot(vec_w, vec_axis) / np.linalg.norm(vec_axis)
        result += res
        
    return result / len(valid_words)
        


def generate_concept_axis(wv, poswords, negwords):
    """
    生成概念轴向量。

    参数:
    - wv(KeyedVectors): 包含预训练的词向量。
    - poswords(list): 第一个词语列表，表示概念的正义词。
    - negwords(list): 第二个词语列表，表示概念的反义词。

    返回:
    - concept_axis: 标准化后的概念轴向量，表示从概念2到概念1的方向。
    """
    # 计算两个概念的平均向量
    pos_vector = wv.get_mean_vector(poswords)
    neg_vector = wv.get_mean_vector(negwords)

    # 计算概念轴
    concept_axis = pos_vector - neg_vector

    # 检查是否为零向量
    norm = np.linalg.norm(concept_axis)
    if norm == 0:
        raise ValueError("Concept axis is a zero vector. Check input words for redundancy or similarity.")

    # 标准化向量
    concept_axis_normalized = concept_axis / norm
    
    return concept_axis_normalized



def intersection_align_gensim(wv1, wv2, words=None):
    """
    计算两个gensim模型的交集，只保留两个模型的共有的词。

    Args:
        wv1 (KeyedVectors):  模型1的KeyedVectors
        wv2 (KeyedVectors): 模型2的KeyedVectors
        words (list, optional): 是否根据词典words对模型进行对齐， 对齐结束后的模型中含有的词不会超出words的范围； 默认None.

    Returns:
        List(KeyedVectors): 
    """

    # Get the vocab for each model
    vocab_wv1 = set(wv1.index_to_key)
    vocab_wv2 = set(wv2.index_to_key)
    #vocab_wv1 = set(wv1.wv.index_to_key)
    #vocab_wv2 = set(wv2.wv.index_to_key)

    # Find the common vocabulary
    common_vocab = vocab_wv1 & vocab_wv2
    if words: common_vocab &= set(words)

    # If no alignment necessary because vocab is identical...
    if not vocab_wv1 - common_vocab and not vocab_wv2 - common_vocab:
        return (wv1,wv2)

    # Otherwise sort by frequency (summed for both)
    common_vocab = list(common_vocab)
    common_vocab.sort(key=lambda w: wv1.get_vecattr(w, "count") + wv2.get_vecattr(w, "count"), reverse=True)
    # print(len(common_vocab))

    # Then for each model...
    for wvn in [wv1, wv2]:
        # Replace old syn0norm array with new one (with common vocab)
        indices = [wvn.key_to_index[w] for w in common_vocab]
        old_arr = wvn.vectors
        new_arr = np.array([old_arr[index] for index in indices])
        wvn.vectors = new_arr

        # Replace old vocab dictionary with new one (with common vocab)
        # and old index2word with new one
        new_key_to_index = {}
        new_index_to_key = []
        for new_index, key in enumerate(common_vocab):
            new_key_to_index[key] = new_index
            new_index_to_key.append(key)
        wvn.key_to_index = new_key_to_index
        wvn.index_to_key = new_index_to_key

    return (wv1,wv2)


def procrustes_align(base_wv, other_wv, words=None):
    """
    使用Procrustes算法对齐两个嵌入模型，以方便进行两个模型中语义比较的数据分析
    
    参考资料: 
       https://github.com/williamleif/histwords
       https://gist.github.com/quadrismegistus/09a93e219a6ffc4f216fb85235535faf
    
    Args:
        base_wv (gensim.models.keyedvectors.KeyedVectors): 基准语言模型
        other_wv (gensim.models.keyedvectors.KeyedVectors): 其他语言模型
        words (list, optional): 是否根据词典words对模型进行对齐， 对齐结束后的模型中含有的词不会超出words的范围； 默认None.
        
    Returns:
        _type_: _description_
    """

    # patch by Richard So [https://twitter.com/richardjeanso) (thanks!) to update this code for new version of gensim
    # base_wv.init_sims(replace=True)
    # other_wv.init_sims(replace=True)

    # make sure vocabulary and indices are aligned
    in_base_wv, in_other_wv = intersection_align_gensim(base_wv, other_wv, words=words)

    # re-filling the normed vectors
    in_base_wv.fill_norms(force=True)
    in_other_wv.fill_norms(force=True)

    # get the (normalized) embedding matrices
    base_vecs = in_base_wv.get_normed_vectors()
    other_vecs = in_other_wv.get_normed_vectors()

    # just a matrix dot product with numpy
    m = other_vecs.T.dot(base_vecs) 
    # SVD method from numpy
    u, _, v = np.linalg.svd(m)
    # another matrix operation
    ortho = u.dot(v) 
    # Replace original array with modified one, i.e. multiplying the embedding matrix by "ortho"
    other_wv.vectors = (in_other_wv.vectors).dot(ortho)    
    
    return other_wv



def semantic_centroid(wv, words):
    """
    计算多个词语的语义中心向量
    
    Args:
        wv (gensim.models.keyedvectors.KeyedVectors): 词向量模型
        words (list): 词语列表

    Returns:
        np.array: 语义中心向量
    """
    container = np.zeros(wv.vector_size)
    valid_words = 0  # 记录有效词的数量

    for word in words:
        try:
            container += wv.get_vector(word)
            valid_words += 1
        except KeyError:  # 忽略不在模型中的词
            continue
    if valid_words == 0:  # 如果没有有效词，返回零向量
        return container

    centroid = container / valid_words
    # 归一化语义中心向量
    norm_centroid = centroid / np.linalg.norm(centroid) if np.linalg.norm(centroid) != 0 else centroid
    return norm_centroid



    
def sematic_projection(wv, words, poswords, negwords, cosine=False, return_full=True):
    """
    计算词语在概念向量上的投影长度。 投影长度大于0表示语义上更接近poswords。
    
    注意概念向量轴是由poswords和negwords定义的。
   
    参考Grand, G., Blank, I.A., Pereira, F. and Fedorenko, E., 2022. Semantic projection recovers rich human knowledge of multiple object features from word embeddings. _Nature Human Behaviour_, pp.1-13.

    Args:
        wv (gensim.models.keyedvectors.KeyedVectors):  词向量模型
        words (list): 词语列表; animals = ['cat', 'dog', 'mouse']
        poswords (list): 词语列表;  poswords = ["large", "big", "huge"]
        negwords (list): 词语列表;  negwords = ["small", "little", "tiny"]
        cosine (bool): 是否使用余弦相似度，默认为False，返回投影值；True时返回余弦相似度
        return_full (bool): 是否返回完整元组列表，默认为True
        

    Returns:
        list: 词语在概念向量上的投影长度列表
    """

    proj_scores = []
    #确保词语在向量模型中
    concept_vector = wv.get_mean_vector(poswords) - wv.get_mean_vector(negwords)
    concept_vector_norm = np.linalg.norm(concept_vector)
    for word in words:
        try:
            any_vector = wv.get_vector(word)
        except KeyError:
            any_vector = np.zeros(wv.vector_size)
        if cosine:
            norm_any = np.linalg.norm(any_vector)
            norm_concept = concept_vector_norm
            denominator = norm_any * norm_concept
            if denominator == 0:
                proj_score = 0.0
            else:
                proj_score = np.dot(any_vector, concept_vector) / denominator
        else:
            proj_score = np.dot(any_vector, concept_vector) / concept_vector_norm
        
        proj_scores.append((word, round(proj_score, 2)))

    if return_full:
        return proj_scores
    else:
        return [score for _, score in proj_scores]

    
def sematic_distance(wv, words1, words2):
    """
    计算语义距离。 

    Args:
        wv (gensim.models.keyedvectors.KeyedVectors): 词向量模型
        words1 (list):   词语列表;  words1 = ['program','software', 'computer']
        words2 (list):   词语列表;  words2 = ["man", "he", "him"]
        
    Returns:
        float: 语义距离
    """
    words1_vector = wv.get_mean_vector(words1)
    words2_vector = wv.get_mean_vector(words2)
    dist = np.linalg.norm(words1_vector - words2_vector)
    return round(dist, 2)




def divergent_association_task(wv, words, minimum=7):
    """
    计算DAT分数

    参考资料:
        Olson, J. A., Nahas, J., Chmoulevitch, D., Cropper, S. J., & Webb, M. E. (2021). Naming unrelated words predicts creativity. Proceedings of the National Academy of Sciences, 118(25), e2022340118.

    Args:
        wv (gensim.models.keyedvectors.KeyedVectors): 词向量模型
        words (list): 词语列表;  words = ['program', 'software', 'computer']
        minimum (int, optional):  词语列表长度; Defaults to 7.

    Returns:
        float: DAT分数
    """
  
    # Keep only valid unique words
    uniques = []
    for word in words:
        try:
            wv.get_vector(word)
            uniques.append(word)
        except:
            pass
    

    # Keep subset of words
    if len(uniques) >= minimum:
        subset = uniques[:minimum]
    else:
        return None # Not enough valid words

    # Compute distances between each pair of words
    distances = []
    for word1, word2 in itertools.combinations(subset, 2):
        dist = scipy.spatial.distance.cosine(wv.get_vector(word1), wv.get_vector(word2))
        distances.append(dist)

    # Compute the DAT score (average semantic distance multiplied by 100)
    return (sum(distances) / len(distances)) * 100



def discursive_diversity_score(wv, words):
    """
    计算话语多样性得分
    
    参考资料:
        Lix, Katharina, Amir Goldberg, Sameer B. Srivastava, and Melissa A. Valentine. “Aligning differences: Discursive diversity and team performance.” Management Science 68, no. 11 (2022): 8430-8448.

    Args:
        wv (gensim.models.keyedvectors.KeyedVectors):   词向量模型
        words (list): 词语列表;  words = ['program','software', 'computer']

    Returns:
        float: 话语多样性得分
    """

    # 计算词嵌入向量的平均值
    embedding_vectors = []
    for word in words:
        try:
            embedding_vectors.append(wv.get_vector(word))
        except:
            pass
    centroid = np.mean(embedding_vectors, axis=0)
    
    # 计算词嵌入向量之间的余弦相似度
    pairwise_distances = [np.dot(centroid, embedding) / (np.linalg.norm(centroid) * np.linalg.norm(embedding)) for embedding in embedding_vectors]
    
    # 计算语言多样性得分
    diversity_score = np.mean(pairwise_distances)
    
    return diversity_score









###########################WEPA#########################################


# 为了能缓存numpy数组，需要先定义一个转换函数
def _array_hash(arr):
    """将numpy数组转换为可哈希的元组"""
    return tuple(arr.flatten())

# 使用类来管理缓存，避免修改numpy内置类型
class ConceptAxisCache:
    def __init__(self):
        self.cache = {}
        
    def get_cached_axis(self, wv, poswords, negwords):
        # 创建缓存键
        key = (_array_hash(wv.vectors[0]) if hasattr(wv, 'vectors') else id(wv), 
               tuple(poswords), tuple(negwords))
        
        # 检查缓存中是否存在
        if key not in self.cache:
            # 计算并缓存概念轴
            self.cache[key] = generate_concept_axis(wv=wv, poswords=poswords, negwords=negwords)
            
        return self.cache[key]

# 创建全局缓存实例
_concept_axis_cache = ConceptAxisCache()



def wepa(wv, text, poswords, negwords, lang='chinese', cosine=False):
    """
    计算文本在概念轴上的投影得分（优化版，内部自动缓存概念轴）
    
    参数:
        wv (KeyedVectors): 语言模型的KeyedVectors
        text (str): 单个文本字符串
        poswords (list): 正面词列表
        negwords (list): 负面词列表
        lang (str): 语言，支持'chinese'或'english'，默认为'chinese'
        cosine (bool): 是否使用余弦相似度，默认为False
    
    返回:
        float: wepa得分
    """
    # 计算概念轴（使用缓存机制）
    axis_vec = _concept_axis_cache.get_cached_axis(wv, poswords, negwords)
    
    # 处理单个文本
    text = clean_text(text=text, lang=lang)
    proj_score = project_text(wv=wv, text=text, axis=axis_vec, lang=lang, cosine=cosine)
    return proj_score