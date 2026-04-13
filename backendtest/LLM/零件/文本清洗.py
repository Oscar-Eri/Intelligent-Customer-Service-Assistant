"""
【功能】文本清洗工具（来自cntext的clean_text和fix_text函数）

【用途】
- 清理文本中的特殊字符、多余空格
- 繁体转简体
- 全角转半角
- 修复混乱编码

【使用示例】
    from 零件.文本清洗 import clean_text, traditional_to_simplified
    
    # 示例1: 基础清洗
    text = "  这个  产品  很好  "
    cleaned = clean_text(text)
    print(cleaned)  # "这个产品很好"
    
    # 示例2: 繁体转简体
    trad = "這個產品很好"
    simple = traditional_to_simplified(trad)
    print(simple)  # "这个产品很好"

【提供的函数】
1. clean_text(text, lang='chinese') - 基础文本清洗
2. traditional_to_simplified(text) - 繁体转简体
3. fix_fullwidth_to_halfwidth(text) - 全角转半角

【原始来源】
- cntext库: cntext/io/utils.py
- 函数名: clean_text(), traditional2simple(), fix_text()
"""
import re


def clean_text(text: str, lang: str = 'chinese') -> str:
    """
    清洗文本：去除多余空格、特殊字符等
    
    Args:
        text: 待清洗的文本
        lang: 语言类型 ('chinese' 或 'english')
    
    Returns:
        str: 清洗后的文本
    """
    if not text:
        return ""
    
    # 去除首尾空格
    text = text.strip()
    
    if lang == 'chinese':
        # 中文：去除多余空格（保留词语间的必要空格）
        text = re.sub(r'\s+', '', text)
        
        # 去除特殊字符（保留中文、英文、数字、常见标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？、；：""''（）《》\s]', '', text)
        
    else:  # english
        # 英文：多个空格合并为一个
        text = re.sub(r'\s+', ' ', text)
        
        # 去除特殊字符（保留英文、数字、常见标点）
        text = re.sub(r'[^\w\s.,!?;:\'"()-]', '', text)
    
    return text


def traditional_to_simplified(text: str) -> str:
    """
    繁体字转简体字
    
    使用简单的映射表进行转换
    注意：这是一个简化版本，完整转换需要使用opencc库
    
    Args:
        text: 繁体中文文本
    
    Returns:
        str: 简体中文文本
    """
    # 常用繁简对照表（部分）
    trad_to_simple = {
        '這': '这', '個': '个', '麼': '么', '為': '为', '會': '会',
        '對': '对', '說': '说', '還': '还', '於': '于', '時': '时',
        '從': '从', '將': '将', '過': '过', '發': '发', '後': '后',
        '裡': '里', '並': '并', '們': '们', '現': '现', '樣': '样',
        '與': '与', '關': '关', '請': '请', '問': '问', '題': '题',
        '體': '体', '點': '点', '開': '开', '機': '机', '網': '网',
        '電': '电', '車': '车', '門': '门', '間': '间', '國': '国',
        '來': '来', '東': '东', '長': '长', '進': '进', '學': '学',
        '實': '实', '認': '认', '證': '证', '讓': '让', '邊': '边',
        '產': '产', '業': '业', '經': '经', '營': '营', '務': '务',
        '質': '质', '優': '优', '價': '价', '購': '购', '賣': '卖',
        '買': '买', '費': '费', '賬': '账', '號': '号', '碼': '码',
        '頭': '头', '麵': '面', '裏': '里', '餘': '余', '醜': '丑',
    }
    
    result = []
    for char in text:
        result.append(trad_to_simple.get(char, char))
    
    return ''.join(result)


def fix_fullwidth_to_halfwidth(text: str) -> str:
    """
    全角字符转半角字符
    
    Args:
        text: 包含全角字符的文本
    
    Returns:
        str: 转换为半角的文本
    """
    result = []
    for char in text:
        code = ord(char)
        # 全角空格
        if code == 0x3000:
            result.append(' ')
        # 其他全角字符 (FF01-FF5E)
        elif 0xFF01 <= code <= 0xFF5E:
            result.append(chr(code - 0xFEE0))
        else:
            result.append(char)
    
    return ''.join(result)


if __name__ == '__main__':
    # 测试
    print("=" * 70)
    print("文本清洗工具测试".center(60))
    print("=" * 70 + "\n")
    
    # 测试1: 基础清洗
    print("【测试1: 基础清洗】")
    dirty_text = "  这个   产品  很好  ，  但是  物流  太慢  了  "
    cleaned = clean_text(dirty_text, lang='chinese')
    print(f"原文: '{dirty_text}'")
    print(f"清洗后: '{cleaned}'\n")
    
    # 测试2: 繁体转简体
    print("【测试2: 繁体转简体】")
    trad_text = "這個產品質量很好，但是物流太慢了"
    simple_text = traditional_to_simplified(trad_text)
    print(f"繁体: {trad_text}")
    print(f"简体: {simple_text}\n")
    
    # 测试3: 全角转半角
    print("【测试3: 全角转半角】")
    fullwidth_text = "ｈｅｌｌｏ　ｗｏｒｌｄ！１２３"
    halfwidth_text = fix_fullwidth_to_halfwidth(fullwidth_text)
    print(f"全角: {fullwidth_text}")
    print(f"半角: {halfwidth_text}\n")
