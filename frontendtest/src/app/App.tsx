import { useState, useRef, useEffect } from 'react';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { sendChatMessage, sendChatMessageStream, type Message } from './services/chatApi';
import { AlertCircle, Loader2 } from 'lucide-react';

// API 配置（与 chatApi 共享）
const API_CONFIG = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || '/api', // 使用环境变量或默认代理
};

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [greeting, setGreeting] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 配置项：是否使用流式响应
  const USE_STREAMING = true; // 启用流式响应

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  // 加载时获取 AI 问候语
  useEffect(() => {
    const fetchGreeting = async () => {
      console.log('开始获取问候语...');
      try {
        // 直接使用 baseUrl + /greeting，因为 baseUrl 已经是完整路径或代理路径
        const url = `${API_CONFIG.baseUrl}/greeting`;
        console.log('请求 URL:', url);
        
        const response = await fetch(url);
        console.log('响应状态:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('问候数据:', data);
          
          if (data.greeting) {
            setGreeting(data.greeting);
            
            // 只要有问候语就显示（不管有没有历史总结）
            setMessages(prevMessages => {
              console.log('当前消息数量:', prevMessages.length);
              if (prevMessages.length === 0) {
                const greetingMessage: Message = {
                  role: 'assistant',
                  content: data.greeting,
                  timestamp: new Date(),
                };
                console.log('已添加问候消息到对话框', data);
                return [greetingMessage];
              }
              return prevMessages;
            });
          }
        }
      } catch (err) {
        console.error('Failed to fetch greeting:', err);
      }
    };

    fetchGreeting();
  }, []);

  // 处理发送消息
  const handleSendMessage = async (content: string) => {
    setError(null);

    // 添加用户消息
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      if (USE_STREAMING) {
        // 流式响应模式
        let fullResponse = '';
        setStreamingMessage('');

        await sendChatMessageStream(
          [...messages, userMessage],
          (chunk) => {
            fullResponse += chunk;
            setStreamingMessage(fullResponse);
          },
          () => {
            // 完成时添加AI消息
            const aiMessage: Message = {
              role: 'assistant',
              content: fullResponse,
              timestamp: new Date(),
            };
            setMessages(prev => [...prev, aiMessage]);
            setStreamingMessage('');
            setIsLoading(false);
          },
          (errorMsg) => {
            setError(errorMsg);
            setStreamingMessage('');
            setIsLoading(false);
          }
        );
      } else {
        // 普通响应模式
        const response = await sendChatMessage([...messages, userMessage]);

        if (response.error) {
          setError(response.error);
        } else {
          const aiMessage: Message = {
            role: 'assistant',
            content: response.message,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, aiMessage]);
        }
        setIsLoading(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '发送消息失败');
      setIsLoading(false);
    }
  };

  return (
    <div className="size-full flex flex-col bg-white">
      {/* 头部 */}
      <header className="flex-shrink-0 border-b border-gray-200 bg-white px-4 py-4 sm:px-6">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-xl font-semibold text-gray-900">AI 对话助手</h1>
          <p className="text-sm text-gray-500 mt-1">与AI进行智能对话</p>
        </div>
      </header>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 && !greeting && (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100 mb-4">
                <svg className="w-8 h-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">开始对话</h3>
              <p className="text-gray-500">输入消息开始与 AI 助手对话</p>
            </div>
          )}

          {messages.map((msg, index) => (
            <ChatMessage
              key={index}
              message={msg.content}
              isUser={msg.role === 'user'}
              timestamp={msg.timestamp}
            />
          ))}

          {/* 流式响应中的消息 */}
          {streamingMessage && (
            <ChatMessage
              message={streamingMessage}
              isUser={false}
              timestamp={new Date()}
            />
          )}

          {/* 加载指示器 */}
          {isLoading && !streamingMessage && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center">
                <Loader2 className="w-5 h-5 text-white animate-spin" />
              </div>
              <div className="flex items-center px-4 py-2 bg-gray-100 rounded-2xl rounded-tl-sm">
                <span className="text-gray-500">正在思考...</span>
              </div>
            </div>
          )}

          {/* 错误提示 */}
          {error && (
            <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800">发送失败</p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* 输入区域 */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-white px-4 py-4 sm:px-6">
        <div className="max-w-4xl mx-auto">
          <ChatInput onSend={handleSendMessage} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
}