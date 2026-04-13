"""
工具函数集合 - 基础实用包
包含：时间查询、计算器、天气查询、情感分析
"""
from datetime import datetime
import pytz
import ast
import operator

# 修复导入路径问题
try:
    from config import hefeng_weather_now_url, hefeng_weather_forecast_url, tavily_api_key
except ImportError:
    from backendtest.config import hefeng_weather_now_url, hefeng_weather_forecast_url, tavily_api_key


# ==================== 1. 时间日期工具 ====================

def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """
    获取当前时间
    
    Args:
        timezone: 时区，默认亚洲/上海
    """
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


def get_weekday(date_str: str = None) -> str:
    """
    获取指定日期是星期几
    
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD，默认为今天
    """
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return f"{date_str} 是 {weekdays[date_obj.weekday()]}"
    except Exception as e:
        return f"日期格式错误，请使用 YYYY-MM-DD 格式"


def get_date_info() -> str:
    """
    获取今日详细信息
    """
    tz = pytz.timezone("Asia/Shanghai")
    now = datetime.now(tz)
    weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
    
    return f"今天是 {now.year}年{now.month}月{now.day}日 {weekday}，当前时间 {now.strftime('%H:%M:%S')}"


# ==================== 2. 计算器工具 ====================

def calculate(expression: str) -> str:
    """
    安全计算器 - 支持加减乘除和幂运算
    
    Args:
        expression: 数学表达式字符串，如 "2 + 3 * 4"
    """
    # 定义允许的运算符
    operators_map = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    def eval_node(node):
        """递归计算 AST 节点"""
        if isinstance(node, ast.Num):  # 数字
            return node.n
        elif isinstance(node, ast.Constant):  # Python 3.8+ 的常量
            return node.value
        elif isinstance(node, ast.BinOp):  # 二元运算
            left = eval_node(node.left)
            right = eval_node(node.right)
            op_func = operators_map.get(type(node.op))
            if op_func:
                try:
                    result = op_func(left, right)
                    # 检查是否为有效数字
                    if isinstance(result, (int, float)) and not (isinstance(result, float) and 
                        (result != result or abs(result) == float('inf'))):
                        return result
                except ZeroDivisionError:
                    raise ValueError("除数不能为零")
                except OverflowError:
                    raise ValueError("数值过大")
            raise TypeError("不支持的运算")
        elif isinstance(node, ast.UnaryOp):  # 一元运算
            operand = eval_node(node.operand)
            op_func = operators_map.get(type(node.op))
            if op_func:
                return op_func(operand)
            raise TypeError("不支持的运算")
        else:
            raise TypeError(f"不支持的表达式类型：{type(node)}")
    
    try:
        # 解析表达式
        tree = ast.parse(expression, mode='eval')
        result = eval_node(tree.body)
        
        # 格式化结果
        if isinstance(result, float):
            # 如果是浮点数，保留合理的小数位数
            if result == int(result):
                result = int(result)
            else:
                result = round(result, 6)
        
        return f"{expression} = {result}"
    except Exception as e:
        return f"❌ 计算错误：{str(e)}"


# ==================== 4. Tavily 网络搜索工具 ====================

def tavily_search(query: str, max_results: int = 5) -> str:
    """
    使用 Tavily 搜索引擎进行网络搜索
    
    Args:
        query: 搜索关键词
        max_results: 最大结果数，默认 5 条
    """
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        import os
        
        # 设置 API Key
        os.environ["TAVILY_API_KEY"] = tavily_api_key
        
        # 创建搜索工具实例
        search_tool = TavilySearchResults(max_results=max_results)
        
        # 执行搜索
        results = search_tool.invoke(query)
        
        # 解析结果（处理不同格式的返回）
        if not results:
            return f"未找到关于'{query}'的搜索结果"
        
        # 格式化输出
        summaries = []
        for i, result in enumerate(results[:max_results], 1):
            # 处理不同的返回格式
            if isinstance(result, dict):
                title = result.get('title', '无标题')
                content = result.get('content', '无内容')
                url = result.get('url', '')
            elif isinstance(result, str):
                # 如果直接是字符串，直接使用
                title = f"结果 {i}"
                content = result[:200]  # 限制长度
                url = ''
            else:
                continue
            
            summary = f"{i}. {title}\n   摘要：{content}"
            if url:
                summary += f"\n   链接：{url}"
            summaries.append(summary)
        
        return f"🔍 关于'{query}'的搜索结果:\n\n" + "\n\n".join(summaries)
        
    except ImportError as e:
        return f"❌ Tavily 搜索工具不可用：{str(e)}\n请安装：pip install langchain-tavily"
    except Exception as e:
        return f"❌ 搜索失败：{str(e)}"

def get_weather(city: str) -> str:
    """
    查询城市实时天气（使用 Tavily 网络搜索）
    
    Args:
        city: 城市名称
    """
    try:
        import os
        from langchain_community.tools.tavily_search import TavilySearchResults
        
        # 设置 API Key
        os.environ["TAVILY_API_KEY"] = tavily_api_key
        
        # 构建搜索查询 - 使用更精确的关键词
        query = f"{city}天气 实时温度 气温 摄氏度"
        
        # 创建搜索工具实例，增加结果数量
        search_tool = TavilySearchResults(max_results=5)
        
        # 执行搜索
        results = search_tool.invoke(query)
        
        if not results:
            return f"🔍 未找到关于'{city}'的天气信息"
        
        # 解析搜索结果
        weather_info = []
        for i, result in enumerate(results, 1):
            if isinstance(result, dict):
                title = result.get('title', '')
                content = result.get('content', '')
                url = result.get('url', '')
                
                # 检查是否包含天气相关信息
                has_weather_info = any(kw in content for kw in [
                    '温度', '气温', '℃', '°C', '度', '天气', '多云', '晴', '雨',
                    'weather', 'temperature', 'temp', 'celsius'
                ])
                
                if has_weather_info and len(content) > 20:  # 确保内容有一定长度
                    info = f"📍 {title}\n   {content}"
                    if url:
                        info += f"\n   🔗 {url}"
                    weather_info.append(info)
        
        if weather_info:
            return f"🌤️ {city}天气查询结果:\n\n" + "\n\n".join(weather_info[:3])
        else:
            # 如果没有结构化数据，返回原始搜索结果
            raw_results = []
            for result in results[:2]:
                if isinstance(result, dict):
                    raw_results.append(f"- {result.get('title', '无标题')}")
            
            if raw_results:
                return f"🔍 已搜索'{city}'的天气，找到以下信息:\n\n" + "\n".join(raw_results)
            else:
                return f"🔍 已搜索'{city}'的天气，但未找到具体数据。请尝试其他方式查询。"
        
    except ImportError as e:
        return f"❌ 天气查询工具不可用：{str(e)}\n请安装：pip install langchain-tavily"
    except Exception as e:
        return f"❌ 天气查询失败：{str(e)}"


def get_weather_forecast(city: str, days: int = 3) -> str:
    """
    查询城市天气预报（使用 Tavily 网络搜索）
    
    Args:
        city: 城市名称
        days: 预报天数，默认 3 天
    """
    try:
        import os
        from langchain_community.tools.tavily_search import TavilySearchResults
        
        # 设置 API Key
        os.environ["TAVILY_API_KEY"] = tavily_api_key
        
        # 构建搜索查询
        query = f"{city} 未来{days}天天气预报 气温 降水"
        
        # 创建搜索工具实例
        search_tool = TavilySearchResults(max_results=3)
        
        # 执行搜索
        results = search_tool.invoke(query)
        
        if not results:
            return f"未找到关于'{city}'的天气预报信息"
        
        # 解析搜索结果
        forecast_info = []
        for i, result in enumerate(results, 1):
            if isinstance(result, dict):
                title = result.get('title', '')
                content = result.get('content', '')
                url = result.get('url', '')
                
                # 提取天气预报信息
                if any(kw in content.lower() for kw in ['预报', 'forecast', '天气', '气温', '温度', '降水', 'rain']):
                    forecast_info.append(f"📅 {title}\n   {content[:300]}")
                    if url:
                        forecast_info[-1] += f"\n   链接：{url}"
        
        if forecast_info:
            return f"📅 {city}天气预报查询结果:\n\n" + "\n\n".join(forecast_info[:2])
        else:
            return f"🔍 已搜索'{city}'的天气预报，但未找到具体数据。请尝试其他方式查询。"
        
    except ImportError as e:
        return f"❌ 天气预报查询工具不可用：{str(e)}"
    except Exception as e:
        return f"❌ 天气预报查询失败：{str(e)}"


def analyze_sentiment(text: str, method: str = "llm") -> str:
    """情感分析工具 - 使用自主实现的情感分析器"""
    try:
        from AIchattest.backendtest.LLM.Memory.emotion_analyzer import analyze_sentiment as _analyze_sentiment
        return _analyze_sentiment(text, method)
    except Exception as e:
        return f"❌ 情感分析失败: {str(e)}"


def analyze_emotion(text: str) -> str:
    """细粒度情绪分析"""
    try:
        from AIchattest.backendtest.LLM.Memory.emotion_analyzer import analyze_emotion as _analyze_emotion
        return _analyze_emotion(text)
    except Exception as e:
        return f"❌ 情绪分析失败: {str(e)}"


def analyze_intent(text: str) -> str:
    """
    意图识别 - 判断用户想要什么
    
    Args:
        text: 待分析的文本内容
    """
    try:
        from AIchattest.backendtest.LLM.Memory.emotion_analyzer import analyze_intent as _analyze_intent
        return _analyze_intent(text)
    except Exception as e:
        return f"❌ 意图识别失败: {str(e)}"


def extract_keywords(text: str, top_n: int = 5) -> str:
    """
    关键词提取 - 自动提取文本核心词汇
    
    Args:
        text: 待分析的文本内容
        top_n: 返回前N个关键词,默认5个
    """
    try:
        from AIchattest.backendtest.LLM.Memory.emotion_analyzer import extract_keywords as _extract_keywords
        return _extract_keywords(text, top_n)
    except Exception as e:
        return f"❌ 关键词提取失败: {str(e)}"


def extract_entities(text: str) -> str:
    """
    实体抽取 - 识别文本中的人名、地名、机构名
    
    Args:
        text: 待分析的文本内容
    """
    try:
        from AIchattest.backendtest.LLM.Memory.emotion_analyzer import extract_entities as _extract_entities
        return _extract_entities(text)
    except Exception as e:
        return f"❌ 实体抽取失败: {str(e)}"


# ==================== 工具描述（用于 LLM 理解） ====================

TOOLS_DESCRIPTION = """
可用的工具：
1. get_current_time(timezone: str) - 获取指定时区的当前时间
   示例：get_current_time("Asia/Shanghai")
   
2. get_weekday(date_str: str) - 查询指定日期是星期几
   示例：get_weekday("2024-01-01")
   
3. get_date_info() - 获取今日详细信息（日期、星期、时间）
   
4. calculate(expression: str) - 计算数学表达式
   示例：calculate("2 + 3 * 4"), calculate("100 / 8")
   
5. tavily_search(query: str, max_results: int) - 网络搜索引擎搜索
   示例：tavily_search("今天新闻"), tavily_search("AI 技术", 3)
   
6. get_weather(city: str) - 查询城市实时天气
   示例：get_weather("北京"), get_weather("Shanghai")
   
7. get_weather_forecast(city: str, days: int) - 查询城市天气预报
   示例：get_weather_forecast("北京", 3)
   
8. analyze_sentiment(text: str, method: str) - 情感分析
   示例：analyze_sentiment("这个产品很好用", "dictionary")
   参数说明：
   - text: 待分析文本
   - method: 'dictionary'(词典法，快速) 或 'llm'(大模型法，更准确)
   
9. analyze_emotion(text: str) - 细粒度情绪分析
   示例：analyze_emotion("我今天很开心")
   识别情绪类型：开心、愤怒、悲伤、惊讶、厌恶、恐惧、中性
   
10. analyze_intent(text: str) - 意图识别
    示例：analyze_intent("我想退货")
    识别意图类型：咨询、投诉、表扬、购买、建议、其他
    
11. extract_keywords(text: str, top_n: int) - 关键词提取
    示例：extract_keywords("人工智能在医疗的应用", 3)
    提取文本中最相关的关键词
    
12. extract_entities(text: str) - 实体抽取
    示例：extract_entities("张三在北京的公司工作")
    识别人名、地名、机构名
"""


# ==================== 工具列表（用于 LangChain 绑定） ====================

# 导出给 LangChain 使用的工具列表
AVAILABLE_TOOLS = [
    get_current_time,
    get_weekday,
    get_date_info,
    calculate,
    tavily_search,
    get_weather,
    get_weather_forecast,
    analyze_sentiment,
    analyze_emotion,
    analyze_intent,
    extract_keywords,
    extract_entities,
]
