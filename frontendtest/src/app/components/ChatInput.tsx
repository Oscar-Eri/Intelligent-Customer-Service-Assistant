import { useState, KeyboardEvent } from 'react';
import { Send } from 'lucide-react';
import { Button } from './ui/button';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex gap-2 items-end">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyPress}
        placeholder="输入消息..."
        disabled={disabled}
        rows={1}
        className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed max-h-32 overflow-y-auto"
      />
      <Button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        className="h-12 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg disabled:opacity-50"
      >
        <Send className="w-5 h-5" />
      </Button>
    </div>
  );
}
