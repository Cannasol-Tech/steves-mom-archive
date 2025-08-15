import React from 'react';

export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  reasoning?: string; // optional reasoning attached to assistant replies
  status?: 'sending' | 'sent' | 'failed';
}

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  isTyping?: boolean;
  reasoningText?: string;
}

const MessageList: React.FC<MessageListProps> = ({ messages, isLoading, isTyping, reasoningText }) => {
  return (
    <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 scroll-smooth custom-scrollbar">
      <div className="mx-auto max-w-4xl space-y-6">
        {messages.map((m, index) => {
          const fromUser = m.role === 'user';
          return (
            <div 
              key={m.id} 
              className={`flex items-start gap-2 sm:gap-3 animate-in slide-in-from-bottom-2 duration-500 ${
                fromUser ? 'justify-end' : 'justify-start'
              }`}
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {!fromUser && (
                <div className="relative flex-shrink-0">
                  <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500 via-blue-500 to-purple-500 p-0.5 shadow-lg">
                    <div className="w-full h-full rounded-2xl bg-white flex items-center justify-center">
                      <div className="w-6 h-6 rounded-xl bg-gradient-to-br from-emerald-400 to-blue-500 flex items-center justify-center">
                        <span className="text-white text-xs font-bold">AI</span>
                      </div>
                    </div>
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white shadow-sm animate-pulse"></div>
                </div>
              )}
              
              <div className={`group relative max-w-[90%] sm:max-w-[75%] ${fromUser ? 'order-first' : ''}`}>
                {/* Message bubble */}
                <div
                  className={`relative px-4 py-3 rounded-3xl shadow-lg backdrop-blur-sm transition-all duration-300 hover:shadow-xl dark:shadow-black/20 ${
                    fromUser
                      ? 'bg-gradient-to-br from-blue-500 to-blue-600 text-white ml-auto rounded-br-lg'
                      : 'bg-gradient-to-br from-white via-gray-50 to-white dark:from-secondary-700 dark:via-secondary-700/80 dark:to-secondary-700 border border-gray-200/60 dark:border-secondary-600/60 text-gray-900 dark:text-gray-100 rounded-bl-lg'
                  }`}
                >
                  {/* Subtle glow effect for AI messages */}
                  {!fromUser && (
                    <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-emerald-500/5 via-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  )}
                  
                  <div className="relative z-10">
                    <div className={`text-xs mb-2 flex items-center gap-2 ${
                      fromUser ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'
                    }`}>
                      <span className="font-medium dark:text-gray-200">
                        {fromUser ? 'You' : "Steve's Mom AI"}
                      </span>
                      <span className="opacity-70 dark:opacity-60">•</span>
                      <span className="opacity-70 dark:opacity-60">
                        {m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      {m.status === 'sent' && (
                        <svg className="w-4 h-4 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                      )}
                      {m.status === 'sending' && (
                        <svg className="w-4 h-4 animate-spin text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v.01M12 20v.01M4 12h.01M20 12h.01M6.31 6.31l.01.01M17.69 17.69l.01.01M6.31 17.69l.01-.01M17.69 6.31l.01-.01" /></svg>
                      )}
                      {m.status === 'failed' && (
                        <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 102 0V6zM9 13a1 1 0 112 0 1 1 0 01-2 0z" clipRule="evenodd" /></svg>
                      )}
                      {!fromUser && (
                        <>
                          <span className="opacity-70 dark:opacity-60">•</span>
                          <div className="flex items-center gap-1">
                            <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></div>
                            <span className="text-emerald-600 dark:text-emerald-400 font-medium">Online</span>
                          </div>
                        </>
                      )}
                    </div>
                    
                    <div className={`whitespace-pre-wrap leading-relaxed ${
                      fromUser ? 'text-white' : 'text-gray-800 dark:text-gray-200'
                    }`}>
                      {m.content}
                    </div>
                    
                    {/* Reasoning section for AI messages */}
                    {!fromUser && m.reasoning && (
                      <div className="mt-4 pt-3 border-t border-gray-200/60 dark:border-secondary-600/60">
                        <details className="group/reasoning">
                          <summary className="cursor-pointer select-none text-xs text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 flex items-center gap-2 transition-colors duration-200">
                            <div className="w-2 h-2 rounded-full bg-gradient-to-r from-emerald-400 to-blue-500 animate-pulse"></div>
                            <span className="font-medium dark:text-emerald-300">Show reasoning process</span>
                            <svg 
                              className="w-4 h-4 transition-transform duration-200 group-open/reasoning:rotate-180" 
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </summary>
                          <div className="mt-3 p-4 bg-gradient-to-br from-emerald-50/80 via-blue-50/60 to-purple-50/40 dark:from-emerald-900/40 dark:via-blue-900/30 dark:to-purple-900/20 border border-emerald-200/60 dark:border-emerald-500/30 rounded-2xl backdrop-blur-sm">
                            <div className="text-sm text-emerald-900 dark:text-emerald-100 whitespace-pre-wrap leading-relaxed">
                              {m.reasoning}
                            </div>
                          </div>
                        </details>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Message actions (appear on hover) */}
                <div className={`absolute top-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 ${
                  fromUser ? '-left-12' : '-right-12'
                }`}>
                  <div className="flex flex-col gap-1">
                    <button className="w-8 h-8 rounded-full bg-white/90 dark:bg-secondary-600/90 backdrop-blur-sm shadow-lg border border-gray-200/60 dark:border-secondary-500/60 flex items-center justify-center hover:bg-gray-50 dark:hover:bg-secondary-500 transition-colors duration-200">
                      <svg className="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              {fromUser && (
                <div className="relative flex-shrink-0">
                  <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shadow-lg">
                    <span className="text-white text-sm font-semibold">U</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-start gap-3 animate-in slide-in-from-bottom-2 duration-500">
            <div className="relative flex-shrink-0">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500 via-blue-500 to-purple-500 p-0.5 shadow-lg">
                <div className="w-full h-full rounded-2xl bg-white flex items-center justify-center">
                  <div className="w-6 h-6 rounded-xl bg-gradient-to-br from-emerald-400 to-blue-500 flex items-center justify-center">
                    <span className="text-white text-xs font-bold">AI</span>
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-white shadow-sm animate-pulse"></div>
            </div>
            
            <div className="group relative max-w-[75%]">
              <div className="relative px-4 py-3 rounded-3xl rounded-bl-lg shadow-lg backdrop-blur-sm bg-gradient-to-br from-white via-gray-50 to-white dark:from-secondary-700 dark:via-secondary-700/80 dark:to-secondary-700 border border-gray-200/60 dark:border-secondary-600/60">
                <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-emerald-500/5 via-blue-500/5 to-purple-500/5 animate-pulse"></div>
                
                <div className="relative z-10">
                  <div className="text-xs mb-2 flex items-center gap-2 text-gray-500 dark:text-gray-400">
                    <span className="font-medium dark:text-gray-200">Steve's Mom AI</span>
                    <span className="opacity-70 dark:opacity-60">•</span>
                    <div className="flex items-center gap-1">
                      <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></div>
                      <span className="text-emerald-600 dark:text-emerald-400 font-medium">Thinking...</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 text-gray-600 dark:text-gray-300">
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-gray-300 dark:bg-secondary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-gray-300 dark:bg-secondary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-gray-300 dark:bg-secondary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-gray-500 dark:text-gray-400 animate-pulse">Processing your request...</span>
                  </div>
                  
                  {reasoningText && (
                    <div className="mt-4 pt-3 border-t border-gray-200/60 dark:border-secondary-600/60">
                      <details className="group/reasoning" open>
                        <summary className="cursor-pointer select-none text-xs text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 flex items-center gap-2 transition-colors duration-200">
                        <summary className="cursor-pointer select-none text-xs text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 flex items-center gap-2 transition-colors duration-200">
                        <summary className="cursor-pointer select-none text-xs text-emerald-700 hover:text-emerald-800 flex items-center gap-2 transition-colors duration-200">
                          <div className="w-2 h-2 rounded-full bg-gradient-to-r from-emerald-400 to-blue-500 animate-pulse"></div>
                          <span className="font-medium dark:text-emerald-300">Live reasoning process</span>
                        </summary>
                        <div className="reasoning-glow mt-3 p-4 bg-gradient-to-br from-emerald-50/80 via-blue-50/60 to-purple-50/40 dark:from-emerald-900/40 dark:via-blue-900/30 dark:to-purple-900/20 border border-emerald-200/60 dark:border-emerald-500/30 rounded-2xl backdrop-blur-sm max-h-60 overflow-auto custom-scrollbar">
                          <div className="relative z-10 text-sm text-emerald-900 dark:text-emerald-100 whitespace-pre-wrap leading-relaxed">
                            {reasoningText}
                          </div>
                        </div>
                      </details>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {isTyping && (
          <div className="flex items-start gap-3 animate-in slide-in-from-bottom-2 duration-300">
            <div className="relative flex-shrink-0">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500 via-blue-500 to-purple-500 p-0.5 shadow-lg">
                <div className="w-full h-full rounded-2xl bg-white flex items-center justify-center">
                  <div className="w-6 h-6 rounded-xl bg-gradient-to-br from-emerald-400 to-blue-500 flex items-center justify-center">
                    <span className="text-white text-xs font-bold">AI</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="relative px-4 py-3 rounded-3xl rounded-bl-lg shadow-lg backdrop-blur-sm bg-gradient-to-br from-white via-gray-50 to-white dark:from-secondary-700 dark:via-secondary-700/80 dark:to-secondary-700 border border-gray-200/60 dark:border-secondary-600/60">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 bg-gray-300 dark:bg-secondary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-300 dark:bg-secondary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-300 dark:bg-secondary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageList;
