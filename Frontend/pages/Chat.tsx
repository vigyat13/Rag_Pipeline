import React, { useState, useEffect, useRef, useCallback } from 'react';
import api from "../services/api";

import { Document, AgentMode, ChatResponse, ChatSource } from '../types';
import { Icons } from '../components/Icons';
import { Spinner } from '../components/ui/Spinner';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  metrics?: {
    tokens: number;
    latency: number;
    agent: string;
  };
}

export const Chat: React.FC = () => {
  // Load state from local storage or default
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const saved = localStorage.getItem('chat_messages');
      return saved ? JSON.parse(saved) : [];
    } catch (e) { return []; }
  });
  const [conversationId, setConversationId] = useState<string | undefined>(() => {
    return localStorage.getItem('chat_conversation_id') || undefined;
  });

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [agentMode, setAgentMode] = useState<AgentMode>(AgentMode.DEFAULT);
  const [showDocSelector, setShowDocSelector] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Persistence effects
  useEffect(() => {
    localStorage.setItem('chat_messages', JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    if (conversationId) localStorage.setItem('chat_conversation_id', conversationId);
    else localStorage.removeItem('chat_conversation_id');
  }, [conversationId]);

  // Polling for documents
  const fetchDocs = useCallback(async () => {
    try {
      const data = await api.get<{ documents: Document[] }>('/documents');
      setDocuments(data.documents);
    } catch (e) { console.error("Failed to load docs", e); }
  }, []);

  useEffect(() => {
    fetchDocs();
    const interval = setInterval(fetchDocs, 30000); // Check for new docs every 30s
    return () => clearInterval(interval);
  }, [fetchDocs]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.post<ChatResponse>('/chat/query', {
        query: userMessage.content,
        conversation_id: conversationId,
        selected_document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
        agent_mode: agentMode,
      });

      // Update conversation ID if provided
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      const aiMessage: Message = {
        id: Date.now().toString() + '_ai',
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        metrics: {
          tokens: response.token_usage.total_tokens,
          latency: response.latency_ms,
          agent: response.used_agent_mode,
        },
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        id: Date.now().toString() + '_err',
        role: 'assistant',
        content: `Error: ${err.message || 'Something went wrong.'}`,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    if(confirm("Are you sure you want to clear the conversation history?")) {
      setMessages([]);
      setConversationId(undefined);
      localStorage.removeItem('chat_messages');
      localStorage.removeItem('chat_conversation_id');
    }
  };

  const toggleDocSelection = (id: string) => {
    setSelectedDocIds(prev => 
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    );
  };

  return (
    <div className="flex h-full bg-white dark:bg-gray-900">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative h-full">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 p-4 flex justify-between items-center bg-white dark:bg-gray-800 z-10">
          <div className="flex items-center space-x-4">
             <div className="flex items-center space-x-2">
               <span className="text-gray-500 dark:text-gray-400 text-sm font-medium">Agent:</span>
               <select 
                 value={agentMode}
                 onChange={(e) => setAgentMode(e.target.value as AgentMode)}
                 className="bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white text-sm rounded-lg focus:ring-brand-500 focus:border-brand-500 block p-2"
               >
                 <option value={AgentMode.DEFAULT}>Default (RAG)</option>
                 <option value={AgentMode.RESEARCH}>Research</option>
                 <option value={AgentMode.SUMMARIZER}>Summarizer</option>
                 <option value={AgentMode.BRAINSTORM}>Brainstorm</option>
               </select>
             </div>
          </div>
          <div className="flex items-center space-x-2">
             <button
               onClick={handleClearChat}
               className="p-2 text-gray-400 hover:text-red-500 transition-colors"
               title="Clear Conversation"
             >
               <Icons.Trash className="w-5 h-5" />
             </button>
             <div className="h-6 w-px bg-gray-300 dark:bg-gray-600 mx-2"></div>
             <button 
               onClick={() => setShowDocSelector(!showDocSelector)}
               className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${selectedDocIds.length > 0 ? 'bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300' : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
             >
               <Icons.Documents className="w-4 h-4 mr-2" />
               {selectedDocIds.length > 0 ? `${selectedDocIds.length} docs` : 'All docs'}
             </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-hide">
          {messages.length === 0 && (
             <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
               <Icons.Bot className="w-16 h-16 mb-4 text-gray-400" />
               <h3 className="text-xl font-medium text-gray-700 dark:text-gray-300">How can I help you today?</h3>
               <p className="max-w-md mt-2 text-sm text-gray-500">Ask questions about your documents using our advanced AI agents.</p>
             </div>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] lg:max-w-[75%] rounded-2xl px-5 py-4 ${
                msg.role === 'user' 
                  ? 'bg-brand-600 text-white rounded-br-none' 
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-none border border-gray-200 dark:border-gray-700'
              }`}>
                <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                
                {/* Sources & Metrics for Assistant */}
                {msg.role === 'assistant' && (
                  <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700/50">
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mb-3">
                        <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Sources</p>
                        <div className="flex flex-wrap gap-2">
                          {msg.sources.map((source) => (
                            <div key={source.id} className="group relative bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded px-2 py-1 text-xs text-gray-600 dark:text-gray-300 cursor-help transition-colors hover:border-brand-300 dark:hover:border-brand-700">
                               <div className="flex items-center space-x-1">
                                 <Icons.FileText className="w-3 h-3" />
                                 <span className="truncate max-w-[150px]">{source.filename}</span>
                               </div>
                               {/* Tooltip for snippet */}
                               <div className="hidden group-hover:block absolute bottom-full left-0 mb-2 w-72 bg-gray-900 text-white text-xs rounded-md p-3 z-50 shadow-xl border border-gray-700">
                                 <div className="font-semibold mb-1 border-b border-gray-700 pb-1">{source.filename}</div>
                                 <div className="italic text-gray-300">"{source.snippet.substring(0, 300)}..."</div>
                               </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {msg.metrics && (
                       <div className="flex items-center space-x-4 text-[10px] text-gray-400 uppercase tracking-widest font-mono">
                         <span title="Latency">{(msg.metrics.latency / 1000).toFixed(2)}s</span>
                         <span title="Tokens">{msg.metrics.tokens} tok</span>
                         <span className="text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/20 px-1.5 py-0.5 rounded">{msg.metrics.agent}</span>
                       </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start animate-pulse">
               <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-bl-none px-5 py-4 border border-gray-200 dark:border-gray-700 flex items-center space-x-2">
                 <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                 <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                 <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                 <span className="text-xs text-gray-500 ml-2">Thinking...</span>
               </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
           <form onSubmit={handleSend} className="relative max-w-4xl mx-auto">
             <input
               type="text"
               value={input}
               onChange={(e) => setInput(e.target.value)}
               placeholder="Ask a question about your documents..."
               className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 text-gray-900 dark:text-white rounded-xl pl-4 pr-12 py-4 focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none shadow-sm transition-shadow"
             />
             <button 
               type="submit" 
               disabled={!input.trim() || isLoading}
               className="absolute right-2 top-2 p-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
             >
               <Icons.Send className="w-5 h-5" />
             </button>
           </form>
           <div className="text-center mt-2">
             <p className="text-xs text-gray-400">AI can make mistakes. Check sources.</p>
           </div>
        </div>
      </div>

      {/* Right Sidebar: Document Context Selector (Conditional) */}
      {showDocSelector && (
        <div className="w-80 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col h-full shadow-xl z-20 absolute right-0 md:relative animate-in slide-in-from-right duration-200">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center bg-gray-50 dark:bg-gray-800/50">
            <h3 className="font-semibold text-gray-900 dark:text-white">Context Documents</h3>
            <button onClick={() => setShowDocSelector(false)} className="md:hidden text-gray-500 hover:text-gray-700">
               <Icons.X className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
             {documents.length === 0 ? (
               <div className="p-4 text-center text-sm text-gray-500">No documents found.</div>
             ) : (
               <div className="space-y-1">
                 {documents.map(doc => {
                   const isSelected = selectedDocIds.includes(doc.id);
                   return (
                     <div 
                       key={doc.id}
                       onClick={() => toggleDocSelection(doc.id)}
                       className={`flex items-center p-3 rounded-lg cursor-pointer transition-all border ${
                         isSelected 
                           ? 'bg-brand-50 border-brand-200 dark:bg-brand-900/20 dark:border-brand-800' 
                           : 'hover:bg-gray-50 dark:hover:bg-gray-700 border-transparent'
                       }`}
                     >
                       <div className={`w-4 h-4 rounded border flex items-center justify-center mr-3 ${
                         isSelected ? 'bg-brand-600 border-brand-600' : 'border-gray-300 dark:border-gray-500'
                       }`}>
                         {isSelected && <Icons.Check className="w-3 h-3 text-white" />}
                       </div>
                       <div className="flex-1 min-w-0">
                         <p className={`text-sm font-medium truncate ${isSelected ? 'text-brand-900 dark:text-brand-100' : 'text-gray-700 dark:text-gray-300'}`}>
                           {doc.filename}
                         </p>
                         <div className="flex justify-between items-center mt-1">
                            <p className="text-xs text-gray-400">{new Date(doc.created_at).toLocaleDateString()}</p>
                            {doc.num_chunks && <span className="text-[10px] bg-gray-100 dark:bg-gray-700 text-gray-500 px-1.5 rounded">{doc.num_chunks} chunks</span>}
                         </div>
                       </div>
                     </div>
                   );
                 })}
               </div>
             )}
          </div>
          <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
             <button 
               onClick={() => setSelectedDocIds([])}
               className="w-full text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 underline"
             >
               Clear selection
             </button>
          </div>
        </div>
      )}
    </div>
  );
};
