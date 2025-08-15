import React, { useEffect, useRef, useState } from 'react';
import ChatInterface from '../components/Chat/ChatInterface';
import type { Message } from '../components/Chat/MessageList';
import { startStream, type StreamHandle } from '../services/chatStream';

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
  const [streamingContent, setStreamingContent] = useState<string>('');
  const [streamingActive, setStreamingActive] = useState<boolean>(false);
  const streamRef = useRef<StreamHandle | null>(null);
  const lastPromptRef = useRef<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (e?: React.FormEvent, promptOverride?: string) => {
    if (e) e.preventDefault();
    const prompt = (promptOverride ?? inputValue).trim();
    if (!prompt || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: prompt,
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    lastPromptRef.current = userMessage.content;
    setStreamingContent('');
    setStreamingActive(true);
    // optional: transient reasoning preview during stream
    setReasoningText(
      "Thinking about your request...\n\n1) Parse intent and entities.\n2) Check background Inventory Agent if needed.\n3) Formulate concise answer."
    );

    // Start streaming from backend
    const history = [
      ...messages.slice(-3).map(m => ({ role: m.role as any, content: m.content })),
      { role: 'user' as const, content: userMessage.content }
    ];
    const handle = startStream({
      messages: history,
      model: model.includes('grok') ? 'grok-3-mini' : undefined,
      temperature: 0.2,
      max_tokens: 512,
      onChunk: (t) => setStreamingContent(prev => prev + t),
      onDone: () => {
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            content: (streamingContentRef.current || '(no content)') as string,
            role: 'assistant',
            timestamp: new Date()
          }
        ]);
        cleanupStream();
      },
      onError: (err) => {
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            content: `Error: ${err.message}`,
            role: 'assistant',
            timestamp: new Date()
          }
        ]);
        cleanupStream();
      }
    });
    streamRef.current = handle;
  };

  // Keep a ref of streamingContent for onDone closure
  const streamingContentRef = useRef<string>('');
  useEffect(() => { streamingContentRef.current = streamingContent; }, [streamingContent]);

  const cleanupStream = () => {
    setIsLoading(false);
    setStreamingActive(false);
    setReasoningText(undefined);
    streamRef.current = null;
  };

  const handleCancel = () => {
    if (streamRef.current) {
      streamRef.current.cancel();
    }
    cleanupStream();
  };

  const handleRetry = () => {
    if (!lastPromptRef.current) return;
    // Immediately start a new stream using the last prompt to avoid timing issues
    handleSendMessage(undefined, lastPromptRef.current);
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
      streamingContent={streamingContent}
      streamingActive={streamingActive}
      onRetryStream={handleRetry}
      onCancelStream={handleCancel}
    />
  );
};

export default ChatPage;
