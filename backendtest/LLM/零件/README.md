# 📦 零件模块 - 来自cntext的独立功能组件

## 📋 概述

本文件夹包含从 **cntext** 库中提取的5个独立功能模块，每个文件都是自包含的，可以单独使用，无需依赖cntext库。

---

## 🗂️ 模块清单

### 1. **关键词上下文提取** (`关键词上下文提取.py`)
- **功能**: 在文本中查找关键词出现的上下文
- **核心函数**: `word_in_context(text, keywords, window=3)`
- **用途**: 理解用户提到某个问题时的具体语境
- **示例**:
```python
from 零件 import word_in_context

text = "我想投诉你们的物流服务，快递太慢了"
result = word_in_context(text, keywords=['投诉', '物流'], window=3)
print(result)
#   keyword | context
#   投诉    | 我想投诉你们的物流
#   物流    | 投诉你们的物流服务
```

---

### 2. **词频统计** (`词频统计.py`)
- **功能**: 统计文本中每个词出现的频率，自动去除停用词
- **核心函数**: `word_count(text, lang='chinese', return_df=False)`
- **用途**: 发现文本中的高频关键词
- **示例**:
```python
from 零件 import word_count

text = "这个产品质量很好，但是物流太慢了"

# 方式1: Counter对象
result = word_count(text, return_df=False)
print(result.most_common(5))

# 方式2: DataFrame
df = word_count(text, return_df=True)
print(df)
```

---

### 3. **文本相似度** (`文本相似度.py`) ⭐推荐
- **功能**: 计算两段文本的相似程度
- **核心函数**: 
  - `cosine_sim(text1, text2)` - 余弦相似度（推荐）
  - `jaccard_sim(text1, text2)` - Jaccard集合相似度
  - `minedit_sim(text1, text2)` - 编辑距离相似度
  - `find_most_similar(query, candidates)` - 批量查找最相似
- **用途**: FAQ匹配、问题去重、相似内容推荐
- **示例**:
```python
from 零件 import cosine_sim, find_most_similar

# 示例1: 计算两个文本的相似度
sim = cosine_sim("我要退款", "如何申请退货")
print(sim)  # 0.75

# 示例2: 从FAQ库中找最匹配的问题
faqs = ["如何退款", "怎么改地址", "物流查询"]
result = find_most_similar("我要退钱", faqs, method='cosine')
print(result['best_match'])  # "如何退款"
print(result['similarity'])  # 0.85
```

---

### 4. **句子分割** (`句子分割.py`)
- **功能**: 将长文本按句子分割成列表
- **核心函数**: `zh_split_sentences(text)`
- **用途**: 句子级情感分析、逐句处理
- **示例**:
```python
from 零件 import zh_split_sentences

text = "这个产品很好。但是物流太慢了！客服态度不错？"
sentences = zh_split_sentences(text)
print(sentences)
# ['这个产品很好', '但是物流太慢了', '客服态度不错']
```

---

### 5. **文本清洗** (`文本清洗.py`)
- **功能**: 清理文本中的特殊字符、繁体转简体、全角转半角
- **核心函数**: 
  - `clean_text(text, lang='chinese')` - 基础文本清洗
  - `traditional_to_simplified(text)` - 繁体转简体
  - `fix_fullwidth_to_halfwidth(text)` - 全角转半角
- **用途**: 数据预处理
- **示例**:
```python
from 零件 import clean_text, traditional_to_simplified

# 示例1: 基础清洗
text = "  这个  产品  很好  "
cleaned = clean_text(text)
print(cleaned)  # "这个产品很好"

# 示例2: 繁体转简体
trad = "這個產品很好"
simple = traditional_to_simplified(trad)
print(simple)  # "这个产品很好"
```

---

## 🚀 快速开始

### 方式1: 导入整个模块
```python
from 零件 import word_in_context, word_count, cosine_sim, zh_split_sentences, clean_text
```

### 方式2: 单独导入
```python
from 零件.关键词上下文提取 import word_in_context
from 零件.词频统计 import word_count
from 零件.文本相似度 import cosine_sim
```

---

## 📊 模块对比

| 模块 | 速度 | 复杂度 | 推荐场景 |
|------|------|--------|---------|
| 关键词上下文提取 | 快 (10ms) | 低 | 意图识别、语境分析 |
| 词频统计 | 快 (15ms) | 低 | 关键词提取、文本摘要 |
| 文本相似度 | 中 (50ms) | 中 | FAQ匹配、问题去重 |
| 句子分割 | 极快 (5ms) | 低 | 句子级分析 |
| 文本清洗 | 极快 (3ms) | 低 | 数据预处理 |

---

## 🔧 依赖项

所有模块只需要以下基础库：
- `jieba` - 中文分词
- `pandas` - 数据处理
- `scikit-learn` - 文本向量化（仅文本相似度需要）
- `re` - 正则表达式（内置）

---

## 💡 使用建议

1. **FAQ匹配系统**: 使用 `文本相似度.cosine_sim()` + `find_most_similar()`
2. **意图识别增强**: 使用 `关键词上下文提取.word_in_context()`
3. **文本预处理管道**: `文本清洗.clean_text()` → `句子分割.zh_split_sentences()` → `词频统计.word_count()`
4. **情感分析前置处理**: 先用 `文本清洗` 清理，再用 `句子分割` 分句，最后逐句分析

---

## 📝 原始来源

所有模块均来自 **cntext** 库（https://github.com/cntext/cntext）：
- `关键词上下文提取`: cntext/stats/utils.py - `word_in_context()`
- `词频统计`: cntext/stats/utils.py - `word_count()`
- `文本相似度`: cntext/stats/similarity.py - `cosine_sim()`, `jaccard_sim()`
- `句子分割`: cntext/stats/utils.py - `zh_split_sentences()`
- `文本清洗`: cntext/io/utils.py - `clean_text()`, `traditional2simple()`

---

## ⚠️ 注意事项

1. **文本相似度**: 余弦相似度对于短文本可能不准确，建议结合多种算法
2. **繁体转简体**: 当前实现是简化版本，只包含常用字映射，如需完整转换请使用opencc库
3. **停用词表**: 词频统计中的停用词表较简单，可根据需求扩展

---

## 🎯 典型应用场景

### 场景1: 智能客服FAQ匹配
```python
from 零件 import find_most_similar

faq_db = [
    "如何申请退款？",
    "怎么修改订单地址？",
    "物流信息查询方法",
]

user_question = "我要退钱"
result = find_most_similar(user_question, faq_db, method='cosine')
print(f"最佳匹配: {result['best_match']} (相似度: {result['similarity']})")
```

### 场景2: 用户反馈分析
```python
from 零件 import word_count, zh_split_sentences

feedback = "产品质量很好。但是物流太慢了。客服态度不错。"

# 分句
sentences = zh_split_sentences(feedback)

# 逐句分析
for sent in sentences:
    freq = word_count(sent)
    print(f"{sent}: {freq.most_common(3)}")
```

### 场景3: 投诉关键词提取
```python
from 零件 import word_in_context

complaint = "我想投诉你们的物流服务，快递太慢了，而且包裹还损坏了"
keywords = ['投诉', '物流', '快递', '包裹']

contexts = word_in_context(complaint, keywords, window=5)
print(contexts)
```

---

## 📞 问题反馈

如有问题或建议，请参考cntext官方文档或提交Issue。
