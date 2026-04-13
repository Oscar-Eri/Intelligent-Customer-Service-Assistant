"""
LLM Provider 抽象层
统一不同 LLM API 的调用接口,支持流式和非流式响应
高内聚低耦合设计,可轻松切换不同的 LLM 提供商
"""
from typing import AsyncIterator, List, Dict, Optional
import httpx
import json
import codecs


class UnifiedLLMProvider:
    """
    统一的 LLM 提供者
    
    支持的提供商:
    - OpenAI (GPT-4, GPT-3.5)
    - Google Gemini
    - Anthropic Claude
    - 任何兼容 OpenAI 格式的 API (如通义千问、智谱等)
    
    使用示例:
        provider = UnifiedLLMProvider(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="your-api-key",
            model="qwen-plus"
        )
        
        async for chunk in provider.chat_completion(messages, stream=True):
            print(chunk)
    """
    
    def __init__(self, base_url: str, api_key: str, model: str, temperature: float = 0.5, max_tokens: int = 4000):
        """
        初始化 LLM 提供者
        
        Args:
            base_url: API 基础 URL (例如: https://api.openai.com/v1)
            api_key: API 密钥
            model: 模型名称 (例如: gpt-4, qwen-plus)
            temperature: 温度参数 (0-1, 控制随机性)
            max_tokens: 最大 token 数
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # 自动补全 chat completions 端点
        if '/chat/completions' not in base_url:
            self.api_url = f"{base_url}/chat/completions"
        else:
            self.api_url = base_url
        
        print(f"🤖 LLM Provider 初始化完成")
        print(f"   模型: {model}")
        print(f"   URL: {self.api_url}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """
        聊天补全接口
        
        Args:
            messages: 消息列表,格式为 [{"role": "user", "content": "..."}]
            tools: 工具定义列表(可选),用于 Function Calling
            stream: 是否使用流式输出
            
        Yields:
            JSON 字符串,格式为:
            - {"type": "content", "content": "文本内容"}
            - {"type": "tool_calls", "tool_calls": [...]}
            
        Example:
            >>> messages = [{"role": "user", "content": "你好"}]
            >>> async for chunk in provider.chat_completion(messages):
            ...     data = json.loads(chunk)
            ...     if data["type"] == "content":
            ...         print(data["content"])
        """
        headers = {
            "Content-Type": "application/json",
        }
        
        # 添加 API Key
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # 构建请求体
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "stream": stream
        }
        
        # 新模型使用 max_completion_tokens,旧模型使用 max_tokens
        if "gpt-5" in self.model or "o1" in self.model:
            payload["max_completion_tokens"] = self.max_tokens
        else:
            payload["max_tokens"] = self.max_tokens
        
        # 添加工具定义
        if tools:
            payload["tools"] = tools
        
        print(f"[DEBUG] 调用 LLM API: {self.api_url}")
        print(f"[DEBUG] 模型: {self.model}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if stream:
                    # 流式响应
                    async with client.stream("POST", self.api_url, json=payload, headers=headers) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            print(f"[ERROR] API 错误 {response.status_code}: {error_text.decode('utf-8')}")
                            yield json.dumps({
                                "type": "content",
                                "content": f"API 错误: {response.status_code}"
                            })
                            return
                        
                        response.raise_for_status()
                        
                        buffer = ""
                        decoder = codecs.getincrementaldecoder('utf-8')(errors='ignore')
                        
                        async for chunk_bytes in response.aiter_bytes():
                            # 解码字节流
                            decoded_chunk = decoder.decode(chunk_bytes, False)
                            buffer += decoded_chunk
                            
                            # 按行处理
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = line.strip()
                                
                                # 跳过空行和非 data 行
                                if not line or not line.startswith("data:"):
                                    continue
                                
                                data = line[5:].strip()
                                
                                # 结束标记
                                if data == "[DONE]":
                                    break
                                
                                try:
                                    chunk = json.loads(data)
                                    
                                    if "choices" in chunk and len(chunk["choices"]) > 0:
                                        delta = chunk["choices"][0].get("delta", {})
                                        
                                        # 工具调用
                                        if "tool_calls" in delta:
                                            yield json.dumps({
                                                "type": "tool_calls",
                                                "tool_calls": delta["tool_calls"]
                                            })
                                        # 文本内容
                                        elif "content" in delta and delta["content"]:
                                            yield json.dumps({
                                                "type": "content",
                                                "content": delta["content"]
                                            })
                                except json.JSONDecodeError as e:
                                    print(f"[DEBUG] JSON 解析错误: {e}")
                                    continue
                        
                        # 处理剩余缓冲区
                        final_chunk = decoder.decode(b'', True)
                        if final_chunk:
                            buffer += final_chunk
                
                else:
                    # 非流式响应
                    response = await client.post(self.api_url, json=payload, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0]["message"].get("content", "")
                        yield json.dumps({"type": "content", "content": content})
        
        except httpx.ConnectError as e:
            print(f"[ERROR] 连接失败: {e}")
            yield json.dumps({"type": "content", "content": f"连接错误: {str(e)}"})
        except Exception as e:
            print(f"[ERROR] 未知错误: {e}")
            yield json.dumps({"type": "content", "content": f"错误: {str(e)}"})


def create_qwen_provider(api_key: str = None, model: str = "qwen-plus") -> UnifiedLLMProvider:
    """
    创建通义千问 LLM 提供者
    
    Args:
        api_key: API Key,如果为 None 则从环境变量读取
        model: 模型名称
        
    Returns:
        UnifiedLLMProvider 实例
    """
    from config import qwen_base_url, qwen_api_key
    
    return UnifiedLLMProvider(
        base_url=qwen_base_url,
        api_key=api_key or qwen_api_key,
        model=model,
        temperature=0.5,
        max_tokens=4000
    )
