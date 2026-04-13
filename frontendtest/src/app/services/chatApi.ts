// API 配置
const API_CONFIG = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || '/api', // 从环境变量读取，默认使用代理
  endpoints: {
    chat: '/chat', // 普通响应模式
    chatStream: '/chat/stream', // 流式响应模式
  },
};

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatRequest {
  messages: Array<{ role: string; content: string }>;
  stream?: boolean;
}

export interface ChatResponse {
  message: string;
  error?: string;
}

/**
 * 发送聊天消息（普通模式）
 * 后端应返回格式: { message: string }
 */
export async function sendChatMessage(
  messages: Message[]
): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.chat}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: messages.map(msg => ({
          role: msg.role,
          content: msg.content,
        })),
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return { message: data.message || data.content || '' };
  } catch (error) {
    console.error('Chat API error:', error);
    return {
      message: '',
      error: error instanceof Error ? error.message : '发送消息失败',
    };
  }
}

/**
 * 发送聊天消息（流式模式）
 * 后端应返回 SSE (Server-Sent Events) 或 streaming response
 * 每个数据块格式: data: {"content": "文本片段"}\n\n
 */
export async function sendChatMessageStream(
  messages: Message[],
  onChunk: (text: string) => void,
  onComplete: () => void,
  onError: (error: string) => void
): Promise<void> {
  try {
    const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.chatStream}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: messages.map(msg => ({
          role: msg.role,
          content: msg.content,
        })),
        stream: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('无法读取响应流');
    }

    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        onComplete();
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // 保留最后一个不完整的行
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonStr = line.slice(6).trim();
            if (jsonStr === '[DONE]') {
              onComplete();
              return;
            }
            const data = JSON.parse(jsonStr);
            if (data.content || data.message) {
              onChunk(data.content || data.message);
            }
          } catch (e) {
            // 忽略无法解析的行
            console.warn('Failed to parse SSE line:', line);
          }
        }
      }
    }
  } catch (error) {
    console.error('Stream API error:', error);
    onError(error instanceof Error ? error.message : '流式响应失败');
  }
}

/**
 * 更新API配置
 */
export function updateApiConfig(config: { baseUrl?: string; chatEndpoint?: string; chatStreamEndpoint?: string }) {
  if (config.baseUrl) {
    API_CONFIG.baseUrl = config.baseUrl;
  }
  if (config.chatEndpoint) {
    API_CONFIG.endpoints.chat = config.chatEndpoint;
  }
  if (config.chatStreamEndpoint) {
    API_CONFIG.endpoints.chatStream = config.chatStreamEndpoint;
  }
}
