import React, { useEffect, useRef, useState } from 'react';
import ChatInterface from '../components/Chat/ChatInterface';
import type { Message } from '../components/Chat/MessageList';

const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hello! I\'m Steve\'s Mom AI assistant. I can help you with inventory management, document generation, and email tasks. How can I assist you today?',
      role: 'assistant',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [model, setModel] = useState<string>('grok-3-mini (proxy)');
  const [reasoningText, setReasoningText] = useState<string | undefined>(undefined);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    // Placeholder: show a simulated Grok reasoning preview while waiting.
    // When backend is connected, replace with live reasoning_content updates.
    setReasoningText(
      "Thinking about your request...\n\n1) Parse intent and entities.\n2) Check background Inventory Agent if needed.\n3) Formulate concise answer."
    );

    try {
      const apiBase = (process as any).env?.REACT_APP_API_BASE as string | undefined;
      const chatUrl = apiBase ? `${apiBase}/api/chat` : '/api/chat';
      const body = {
        messages: [
          // Send minimal context: last assistant then user; can expand later
          ...messages.slice(-3).map(m => ({ role: m.role, content: m.content })),
          { role: 'user', content: userMessage.content }
        ],
        model: model.includes('grok') ? 'grok-3-mini' : undefined,
        temperature: 0.2,
        max_tokens: 512,
        stream_reasoning: false
      };

      const res = await fetch(chatUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`API ${res.status}: ${txt}`);
      }

      const data = await res.json();
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.message?.content || '(no content)',
        role: 'assistant',
        timestamp: new Date(),
        // pass through reasoning for collapsible display in MessageList
        reasoning: data.reasoning_content || undefined
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err: any) {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: `Error: ${err?.message || 'Failed to reach AI service'}`,
        role: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
    } finally {
      setIsLoading(false);
      // clear live panel; final reasoning is attached to message.reasoning
      setReasoningText(undefined);
    }
  };

  const handleKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      // trigger submit from keyboard
      const form = (e.currentTarget.closest('form')) as HTMLFormElement | null;
      form?.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    }
  };

  return (
    <ChatInterface
      messages={messages}
      isLoading={isLoading}
      inputValue={inputValue}
      model={model}
      onModelChange={setModel}
      onChangeInput={setInputValue}
      onSubmit={() => handleSendMessage()}
      onKeyDown={handleKeyDown}
      reasoningText={reasoningText}
    />
  );
};

export default ChatPage;
