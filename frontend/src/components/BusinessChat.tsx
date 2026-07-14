import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, AlertCircle, Database, Gauge, HelpCircle } from 'lucide-react';
import { copilotApi } from '../services/api';

interface Message {
  role: 'user' | 'assistant';
  content?: string;
  data?: {
    observation: string;
    evidence: string;
    explanation: string;
    recommendation: string;
    confidence: number;
    metadata: {
      sources_used: string[];
      confidence_score: number;
      reasoning_steps: string[];
      suggested_questions: string[];
    };
  };
}

interface BusinessChatProps {
  onDrillDown: (tab: string) => void;
}

export const BusinessChat: React.FC<BusinessChatProps> = ({ onDrillDown }) => {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello Admin. I am your **JourneyIQ AI Business Copilot**. Query me in natural language regarding revenue drops, catalog stock levels, or customer segmentation. I evaluate live database parameters and model timelines to answer securely.'
    }
  ]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const sessionId = useRef(Math.random().toString(36).substring(7));

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const handleSendMessage = async (msgText: string) => {
    if (!msgText.strip()) return;
    setInput('');
    
    // Add user message
    setHistory(prev => [...prev, { role: 'user', content: msgText }]);
    setLoading(true);

    try {
      const res = await copilotApi.chat(msgText, sessionId.current);
      setHistory(prev => [...prev, {
        role: 'assistant',
        data: {
          observation: res.observation,
          evidence: res.evidence,
          explanation: res.explanation,
          recommendation: res.recommendation,
          confidence: res.confidence,
          metadata: res.metadata
        }
      }]);
    } catch (err) {
      console.error(err);
      setHistory(prev => [...prev, {
        role: 'assistant',
        content: 'Failed to process copilot query. Fallback heuristics: check payment gateway webhook ports or verify SQLite path.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const presetQuestions = [
    "Why did revenue decrease this week?",
    "Which products should I restock?",
    "Which customers are likely to churn?",
    "How is customer satisfaction?"
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-[#111827] p-5 space-y-4 flex flex-col h-[550px] justify-between relative overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-850 pb-3 z-10">
        <div className="flex items-center gap-2">
          <span className="p-1.5 bg-indigo-500/10 rounded-lg text-indigo-400">
            <Sparkles className="w-4 h-4" />
          </span>
          <div>
            <h4 className="text-xs font-bold text-white tracking-tight">AI Business Copilot Chat</h4>
            <p className="text-[9px] text-slate-500 font-semibold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
              NVIDIA NIM grounded pipeline active
            </p>
          </div>
        </div>
      </div>

      {/* Chat Messages Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 py-2 text-xs leading-relaxed max-h-[340px]">
        {history.map((msg, i) => (
          <div 
            key={i} 
            className={`flex flex-col max-w-[90%] ${msg.role === 'user' ? 'ml-auto items-end' : 'mr-auto items-start'}`}
          >
            {msg.role === 'user' ? (
              <div className="p-2.5 rounded-2xl bg-indigo-650 text-white rounded-tr-none">
                <p className="font-semibold">{msg.content}</p>
              </div>
            ) : (
              <div className="space-y-3 w-full">
                {msg.content && (
                  <div className="p-3 rounded-2xl bg-slate-900 border border-slate-850 text-slate-350 rounded-tl-none font-semibold">
                    {msg.content}
                  </div>
                )}
                
                {msg.data && (
                  <div className="rounded-xl border border-slate-850 bg-slate-950 p-4 space-y-3.5 shadow-md">
                    {/* Structure formatting */}
                    <div className="space-y-1">
                      <span className="text-[10px] text-indigo-400 font-extrabold uppercase tracking-wide">Observation</span>
                      <p className="text-white font-bold text-xs">{msg.data.observation}</p>
                    </div>

                    <div className="space-y-1 border-t border-slate-850 pt-2">
                      <span className="text-[10px] text-amber-500 font-extrabold uppercase tracking-wide">Evidence</span>
                      <p className="text-slate-350 font-semibold text-2xs whitespace-pre-wrap">{msg.data.evidence}</p>
                    </div>

                    <div className="space-y-1 border-t border-slate-850 pt-2">
                      <span className="text-[10px] text-cyan-400 font-extrabold uppercase tracking-wide">Explanation</span>
                      <p className="text-slate-400 font-semibold text-2xs">{msg.data.explanation}</p>
                    </div>

                    <div className="space-y-1 border-t border-slate-850 pt-2 flex justify-between items-start">
                      <div className="space-y-1 flex-1">
                        <span className="text-[10px] text-emerald-450 font-extrabold uppercase tracking-wide">Recommendation</span>
                        <p className="text-emerald-400 font-black text-2xs">{msg.data.recommendation}</p>
                      </div>
                      
                      {/* Drill-down action link */}
                      <button
                        onClick={() => {
                          const rec = msg.data!.recommendation.toLowerCase();
                          if (rec.includes('restock') || rec.includes('stock')) onDrillDown('products');
                          else if (rec.includes('coupon') || rec.includes('campaign')) onDrillDown('agent');
                          else onDrillDown('overview');
                        }}
                        className="rounded bg-indigo-650/20 hover:bg-indigo-600 border border-indigo-500/30 text-indigo-400 hover:text-white font-extrabold text-[9px] px-2 py-1 transition-colors uppercase cursor-pointer shrink-0 ml-3"
                      >
                        Show Details
                      </button>
                    </div>

                    {/* Grounded data sources & confidence */}
                    <div className="border-t border-slate-850 pt-2 flex items-center justify-between text-[9px] text-slate-500 font-extrabold uppercase">
                      <span className="flex items-center gap-1">
                        <Database className="w-3 h-3 text-slate-400" />
                        Grounded: {msg.data.metadata.sources_used.join(', ')}
                      </span>
                      <span className="flex items-center gap-1 text-emerald-450 bg-emerald-500/5 px-2 py-0.5 rounded border border-emerald-500/10">
                        <Gauge className="w-3 h-3" />
                        Conf: {msg.data.confidence}%
                      </span>
                    </div>

                    {/* Suggested dynamic follow-up questions */}
                    {msg.data.metadata.suggested_questions && msg.data.metadata.suggested_questions.length > 0 && (
                      <div className="border-t border-slate-850 pt-2 space-y-1.5">
                        <span className="text-[9px] text-slate-500 font-extrabold uppercase block tracking-wider">Suggested follow-ups:</span>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.data.metadata.suggested_questions.map((q, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleSendMessage(q)}
                              className="bg-slate-900 border border-slate-850 hover:bg-slate-800 text-[9px] text-slate-350 px-2 py-1 rounded-full cursor-pointer transition-colors"
                            >
                              {q}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-1 bg-slate-900 p-2.5 rounded-2xl rounded-tl-none w-14 mr-auto border border-slate-850">
            <span className="w-1 h-1 rounded-full bg-indigo-400 animate-bounce [animation-delay:-0.3s]" />
            <span className="w-1 h-1 rounded-full bg-indigo-400 animate-bounce [animation-delay:-0.15s]" />
            <span className="w-1 h-1 rounded-full bg-indigo-400 animate-bounce" />
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Preset Suggestions List */}
      {history.length === 1 && (
        <div className="space-y-1 relative z-10 border-t border-slate-850 pt-2">
          <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">Choose preset analysis:</span>
          <div className="grid grid-cols-2 gap-1.5">
            {presetQuestions.map((q, idx) => (
              <button 
                key={idx}
                onClick={() => handleSendMessage(q)}
                className="text-left text-[9px] bg-slate-900 hover:bg-slate-850 text-slate-300 py-1.5 px-2.5 rounded border border-slate-850 font-semibold truncate cursor-pointer"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Chat Input Field */}
      <div className="flex gap-2 z-10 pt-2 border-t border-slate-850">
        <input 
          type="text" 
          placeholder="Ask Business Copilot..." 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendMessage(input)}
          className="flex-1 bg-slate-950 text-xs border border-slate-850 rounded-lg px-3 py-2 outline-none focus:ring-1 focus:ring-indigo-500 transition-all text-white"
        />
        <button 
          onClick={() => handleSendMessage(input)}
          className="bg-indigo-600 hover:bg-indigo-750 text-white w-9 h-9 flex items-center justify-center rounded-lg transition-all cursor-pointer"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
