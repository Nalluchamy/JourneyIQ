import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageSquare, X, Send, Sparkles, ShoppingBag, Minimize2, Maximize2 } from 'lucide-react';
import { assistantApi } from '../services/api';

interface Product {
  id: number;
  name: string;
  brand?: string;
  price: number;
  rating: number;
  image_url?: string;
  recommendation_engine?: string;
}

interface Message {
  sender: 'user' | 'assistant';
  text: str;
  products?: Product[];
  source?: string;
  engine?: string;
}

export const ChatbotWidget: React.FC = () => {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<Message[]>([
    {
      sender: 'assistant',
      text: 'Hi there! I am your **JourneyIQ AI Shopping Assistant**. How can I help you discover products today?',
    },
  ]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Fetch suggestions autocomplete prompts
    const fetchSuggestions = async () => {
      try {
        const data = await assistantApi.getSuggestions();
        setSuggestions(data.suggestions || []);
      } catch (err) {
        console.error('Failed to load chat suggestions:', err);
      }
    };
    fetchSuggestions();
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory, loading]);

  const handleSendMessage = async (msgText: string) => {
    if (!msgText.trim() || loading) return;
    
    // Add user message
    const userMsg: Message = { sender: 'user', text: msgText };
    setChatHistory((prev) => [...prev, userMsg]);
    setMessage('');
    setLoading(true);

    try {
      const data = await assistantApi.chat(msgText);
      const assistantMsg: Message = {
        sender: 'assistant',
        text: data.reply,
        products: data.products,
        source: data.source,
        engine: data.recommendation_engine,
      };
      setChatHistory((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: Message = {
        sender: 'assistant',
        text: "I'm sorry, I encountered an issue connecting to my processor. Please try again in a few moments.",
      };
      setChatHistory((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleProductClick = (productId: number) => {
    setIsOpen(false);
    navigate(`/products/${productId}`);
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 p-4 bg-brand-gradient hover:scale-105 active:scale-95 text-white rounded-full shadow-2xl shadow-indigo-500/30 flex items-center justify-center transition-all duration-300 border border-white/10"
        aria-label="Open AI Assistant"
      >
        <MessageSquare className="h-6 w-6" />
        <span className="absolute -top-1 -right-1 flex h-3 w-3">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
        </span>
      </button>
    );
  }

  return (
    <div
      className={`fixed bottom-6 right-6 z-40 w-full max-w-sm md:max-w-md bg-[#0f172a]/95 backdrop-blur-md rounded-2xl border border-white/10 shadow-2xl overflow-hidden transition-all duration-300 flex flex-col ${
        isMinimized ? 'h-14' : 'h-[500px] max-h-[85vh]'
      }`}
    >
      {/* Widget Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-brand-gradient text-white border-b border-white/5">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-cyan-300 animate-pulse" />
          <div>
            <span className="font-extrabold text-sm tracking-tight block">AI Shopping Assistant</span>
            <span className="text-[10px] text-cyan-200 font-medium">Powered by JourneyIQ NLP v1.1</span>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-white"
            title={isMinimized ? 'Expand window' : 'Minimize window'}
          >
            {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-white"
            title="Close Assistant"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages Log area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    msg.sender === 'user'
                      ? 'bg-indigo-600 text-white rounded-br-none shadow-md shadow-indigo-600/10'
                      : 'bg-white/5 text-slate-200 border border-white/10 rounded-bl-none'
                  }`}
                >
                  <p className="whitespace-pre-line font-medium">{msg.text}</p>
                  
                  {/* Badge details */}
                  {msg.sender === 'assistant' && (msg.source || msg.engine) && (
                    <div className="mt-2 pt-1.5 border-t border-white/5 flex flex-wrap gap-2 text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                      {msg.source && <span>LLM: {msg.source}</span>}
                      {msg.engine && <span>Engine: {msg.engine}</span>}
                    </div>
                  )}
                </div>

                {/* Returned product embeds */}
                {msg.products && msg.products.length > 0 && (
                  <div className="w-full mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 pl-2">
                    {msg.products.map((prod) => (
                      <div
                        key={prod.id}
                        onClick={() => handleProductClick(prod.id)}
                        className="bg-black/40 hover:bg-black/60 border border-white/5 hover:border-cyan-500/40 p-2.5 rounded-xl flex gap-3 items-center cursor-pointer transition-all active:scale-[0.98]"
                      >
                        {prod.image_url ? (
                          <img
                            src={prod.image_url}
                            alt={prod.name}
                            className="w-10 h-10 rounded-lg object-cover border border-white/5 flex-shrink-0"
                          />
                        ) : (
                          <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center text-slate-400 text-xs flex-shrink-0">
                            📦
                          </div>
                        )}
                        <div className="min-w-0 flex-1">
                          <h4 className="font-bold text-xs text-white truncate">{prod.name}</h4>
                          <div className="flex items-center justify-between mt-1">
                            <span className="text-[11px] font-bold text-cyan-400">${prod.price.toFixed(2)}</span>
                            <span className="text-[10px] text-amber-400 font-semibold">{prod.rating}⭐</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Loading / Typing indicator */}
            {loading && (
              <div className="flex items-start pl-2">
                <div className="bg-white/5 border border-white/10 rounded-2xl rounded-bl-none px-4 py-2 text-xs text-slate-400 font-bold flex items-center gap-1.5 shadow-lg">
                  <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full animate-bounce delay-75" />
                  <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce delay-150" />
                  <span className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce delay-300" />
                  <span>Assistant is thinking...</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Autocomplete Quick Prompts list */}
          {suggestions.length > 0 && (
            <div className="px-4 py-2 border-t border-white/5 bg-black/20 flex gap-2 overflow-x-auto whitespace-nowrap scrollbar-none scroll-smooth">
              {suggestions.map((sug, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(sug)}
                  className="px-3 py-1 bg-white/5 hover:bg-indigo-500/10 border border-white/5 hover:border-indigo-500/30 text-slate-300 hover:text-white rounded-full text-xs font-bold transition-all"
                >
                  {sug}
                </button>
              ))}
            </div>
          )}

          {/* Input Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage(message);
            }}
            className="p-3 border-t border-white/5 bg-black/40 flex gap-2"
          >
            <input
              type="text"
              placeholder="Ask anything (e.g. Recommend a Laptop under $1000)"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="flex-1 px-4 py-2.5 text-sm bg-black/50 border border-white/10 rounded-xl focus:outline-none focus:ring-1 focus:ring-indigo-500 text-white"
            />
            <button
              type="submit"
              disabled={loading || !message.trim()}
              className="p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl flex items-center justify-center transition-colors shadow-lg shadow-indigo-600/20"
            >
              <Send className="h-4.5 w-4.5" />
            </button>
          </form>
        </>
      )}
    </div>
  );
};
