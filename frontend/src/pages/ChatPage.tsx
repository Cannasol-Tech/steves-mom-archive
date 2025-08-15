import React, { useEffect, useRef, useState } from 'react';
import ChatInterface from '../components/Chat/ChatInterface';
import type { Message } from '../components/Chat/MessageList';
import { startStream, type StreamHandle } from '../services/chatStream';
import { connectLiveUpdates, type LiveUpdateConnection } from '../services/socketClient';
import { TaskStatus } from '../types/tasks';

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
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const streamRef = useRef<StreamHandle | null>(null);
  const lastPromptRef = useRef<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const liveConnRef = useRef<LiveUpdateConnection | null>(null);

  const handleApproveTask = async (taskId: string) => {
    await updateTaskStatus(taskId, 'approved');
  };

  const handleRejectTask = async (taskId: string) => {
    await updateTaskStatus(taskId, 'rejected');
  };

  const updateTaskStatus = async (taskId: string, status: 'approved' | 'rejected') => {
    try {
      const apiBaseUrl = process.env.REACT_APP_API_BASE_URL || '';
      const response = await fetch(`${apiBaseUrl}/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to ${status} task`);
      }

            const updatedTask: { id: string, status: TaskStatus } = await response.json();

      setMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.taskId === taskId ? { ...msg, taskStatus: updatedTask.status } : msg
        )
      );
      setToastMessage(`Task successfully ${status}.`);
    } catch (error: any) {
      setToastMessage(`Error: ${error.message}`);
    }
    setTimeout(() => setToastMessage(null), 5000);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Live updates connection: connect on mount, cleanup on unmount
  useEffect(() => {
    const conn = connectLiveUpdates({
      onTaskUpdate: (updatedTask: Message) => {
        setMessages(prevMessages =>
          prevMessages.map(msg =>
            msg.taskId === updatedTask.id ? { ...msg, taskStatus: updatedTask.status } : msg
          )
        );
      },
      onMessage: (text) => {
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + Math.random()).toString(),
            content: text,
            role: 'assistant',
            timestamp: new Date(),
          }
        ]);
      },
      onError: (err) => {
        setToastMessage(`Live updates error: ${err.message}`);
      },
      onClose: () => {
        // no-op for now; could update a connection status indicator
      },
    });
    liveConnRef.current = conn;
    return () => {
      try { conn.disconnect(); } catch {}
      liveConnRef.current = null;
    };
  }, []);

  const handleSendMessage = async (e?: React.FormEvent, promptOverride?: string) => {
    if (e) e.preventDefault();
    const prompt = (promptOverride ?? inputValue).trim();
    if (!prompt || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: prompt,
      role: 'user',
      timestamp: new Date(),
      status: 'sending'
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
    let statusUpdated = false;
    const handle = startStream({
      messages: history,
      model: model.includes('grok') ? 'grok-3-mini' : undefined,
      temperature: 0.2,
      max_tokens: 512,
      onChunk: (t) => {
        if (!statusUpdated) {
          setMessages(prev => {
            const newMessages = [...prev];
            let lastUserMessageIndex = -1;
            for (let i = newMessages.length - 1; i >= 0; i--) {
              if (newMessages[i].role === 'user') {
                lastUserMessageIndex = i;
                break;
              }
            }
            if (lastUserMessageIndex !== -1) {
              const updatedMessage = { ...newMessages[lastUserMessageIndex], status: 'sent' as const };
              newMessages[lastUserMessageIndex] = updatedMessage;
            }
            return newMessages;
          });
          statusUpdated = true;
        }
        setStreamingContent(prev => prev + t);
      },
      onDone: (reasoning?: string) => {
        const content = streamingContentRef.current;
        if (content && content.trim() && content.trim() !== '(no content)') {
          const newTaskId = `task-${Date.now()}`;
          setMessages(prev => [
            ...prev,
            {
              // This is a mock for demonstration. In a real app, the backend would return this.
              id: newTaskId,
              taskId: newTaskId,
              taskStatus: TaskStatus.PENDING_APPROVAL,
              content: content,
              role: 'assistant',
              timestamp: new Date(),
              reasoning: reasoning || undefined
            }
          ]);
        }
        cleanupStream();
      },
      onError: (err) => {
        // Preserve any partial streamed content as a message
        const partial = streamingContentRef.current;
        setMessages(prev => {
          const next = [...prev];
          if (partial && partial.trim().length > 0) {
            next.push({
              id: (Date.now() + 1).toString(),
              content: partial,
              role: 'assistant',
              timestamp: new Date(),
            });
          }
          return next;
        });
        // Show a toast for the error
        setMessages(prev => {
          const newMessages = [...prev];
          let lastUserMessageIndex = -1;
          for (let i = newMessages.length - 1; i >= 0; i--) {
            if (newMessages[i].role === 'user' && newMessages[i].status === 'sending') {
              lastUserMessageIndex = i;
              break;
            }
          }
          if (lastUserMessageIndex !== -1) {
            const updatedMessage = { ...newMessages[lastUserMessageIndex], status: 'failed' as const };
            newMessages[lastUserMessageIndex] = updatedMessage;
          }
          return newMessages;
        });
        setToastMessage(`Network error: ${err.message}`);
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
      toastMessage={toastMessage || undefined}
      onApproveTask={handleApproveTask}
      onRejectTask={handleRejectTask}
    />
  );
};

export default ChatPage;
