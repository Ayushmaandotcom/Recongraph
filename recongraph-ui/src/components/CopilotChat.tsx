"use client";

import React, { useState, useRef, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Citation {
  document_id: string;
  section?: string;
  source?: string;
  text: string;
  effective_date?: string;
}

interface Message {
  role: "user" | "copilot";
  content: string;
  citations?: Citation[];
  confidence?: { level: string; overall: number };
  abstained?: boolean;
  query_type?: string;
  request_id?: string;
}

interface CopilotChatProps {
  context?: { packetId?: string; runId?: string };
}

export default function CopilotChat({ context }: CopilotChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    { role: "copilot", content: "Hello! I am your AI Copilot. You can ask me questions about GST compliance rules or why certain reconciliation decisions were made." }
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});
  
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Open chat when context changes (if a packet is selected for copilot)
  useEffect(() => {
    if (context?.packetId) {
      setIsOpen(true);
    }
  }, [context?.packetId]);

  const toggleCitation = (idx: number, citIdx: number) => {
    const key = `${idx}-${citIdx}`;
    setExpandedCitations(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSend = async (overrideMsg?: string) => {
    const userMsg = overrideMsg || input.trim();
    if (!userMsg) return;
    
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    if (!overrideMsg) setInput("");
    setIsLoading(true);

    try {
      // Build conversation history (last 5 messages)
      const history = messages
        .slice(-5)
        .map(m => ({ role: m.role, content: m.content }));

      const payload = {
        query: userMsg,
        conversation_history: history,
        ...(context?.packetId && { packet_id: context.packetId }),
        ...(context?.runId && { run_id: context.runId })
      };

      const res = await fetch(`${API_URL}/copilot/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error("API request failed");
      
      const data = await res.json();
      setMessages(prev => [...prev, {
        role: "copilot",
        content: data.answer,
        citations: data.citations,
        confidence: data.confidence,
        abstained: data.abstained,
        query_type: data.query_type,
        request_id: data.request_id
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: "copilot", content: "Sorry, I encountered an error connecting to the knowledge base.", abstained: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderConfidenceBadge = (confidence?: { level: string; overall: number }) => {
    if (!confidence) return null;
    const colors: Record<string, string> = {
      HIGH: "bg-green-100 text-green-800 border-green-300",
      MEDIUM: "bg-yellow-100 text-yellow-800 border-yellow-300",
      LOW: "bg-orange-100 text-orange-800 border-orange-300",
      INSUFFICIENT: "bg-red-100 text-red-800 border-red-300",
    };
    const c = colors[confidence.level.toUpperCase()] || "bg-gray-100 text-gray-800 border-gray-300";
    
    return (
      <div className={`mt-2 inline-flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full border ${c}`}>
        CONFIDENCE: {confidence.level}
      </div>
    );
  };

  return (
    <>
      <button 
        onClick={() => setIsOpen(true)}
        className={`fixed bottom-6 right-6 w-14 h-14 bg-[var(--color-primary)] text-white rounded-full shadow-lg flex items-center justify-center transition-transform hover:scale-110 z-40 ${isOpen ? 'hidden' : ''}`}
        title="Open AI Copilot"
      >
        <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 bg-black/20 z-40 lg:hidden" onClick={() => setIsOpen(false)} />
          <div className="fixed top-0 right-0 bottom-0 w-full sm:w-[420px] bg-[var(--color-surface)] border-l border-[var(--color-border)] shadow-2xl flex flex-col z-50 transform transition-transform duration-300 ease-in-out translate-x-0">
            <div className="bg-gradient-to-r from-[var(--color-primary)] to-indigo-600 text-white p-4 flex justify-between items-center shadow-md">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-bold text-lg leading-tight">AI Copilot</h3>
                  <p className="text-xs text-white/80">ReconGraph Assistant</p>
                </div>
              </div>
              <button onClick={() => setIsOpen(false)} className="p-2 text-white/80 hover:text-white hover:bg-white/10 rounded-full transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            {context?.packetId && (
              <div className="bg-[var(--color-surface-hover)] border-b border-[var(--color-border)] p-3 text-sm flex items-center justify-between">
                <span className="flex items-center gap-2 text-[var(--color-text-muted)] font-medium">
                  📋 Viewing Context: <span className="font-mono text-[var(--color-text)]">{context.packetId}</span>
                </span>
                <button 
                  onClick={() => handleSend("Why was this invoice flagged?")}
                  className="text-xs bg-[var(--color-primary)] text-white px-2 py-1 rounded hover:opacity-90 transition-opacity"
                >
                  Ask Why
                </button>
              </div>
            )}
            
            <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-[var(--color-background)]">
              {messages.map((m, idx) => (
                <div key={idx} className={`flex flex-col ${m.role === "user" ? "items-end" : "items-start"}`}>
                  <div className={`max-w-[85%] rounded-2xl p-4 text-sm shadow-sm ${
                    m.role === "user" 
                      ? "bg-[var(--color-primary)] text-white rounded-br-none" 
                      : m.abstained 
                        ? "bg-red-50 border border-red-200 rounded-bl-none text-red-900" 
                        : "bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-bl-none text-[var(--color-text)]"
                  }`}>
                    {m.abstained && <div className="font-bold text-red-700 mb-1 text-xs uppercase">⚠️ Copilot Abstained</div>}
                    <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
                    
                    {m.role === "copilot" && !m.abstained && renderConfidenceBadge(m.confidence)}
                    
                    {m.citations && m.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-[var(--color-border)]/50">
                        <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider block mb-2">Sources</span>
                        <div className="space-y-2">
                          {m.citations.map((c, citIdx) => (
                            <div key={citIdx} className="text-xs">
                              <button 
                                onClick={() => toggleCitation(idx, citIdx)}
                                className="text-left w-full flex items-start gap-1 hover:text-[var(--color-primary)] transition-colors"
                              >
                                <span className="font-mono bg-[var(--color-surface-hover)] px-1 rounded">[{citIdx + 1}]</span> 
                                <span className="font-medium">{c.source || "Document"} {c.section ? `— ${c.section}` : ""}</span>
                              </button>
                              {expandedCitations[`${idx}-${citIdx}`] && (
                                <div className="mt-1 ml-6 p-2 bg-[var(--color-surface)] border border-[var(--color-border)] rounded italic text-[var(--color-text-muted)]">
                                  "{c.text}"
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex items-start">
                  <div className="bg-[var(--color-surface-elevated)] border border-[var(--color-border)] rounded-2xl rounded-bl-none p-4 shadow-sm">
                    <div className="flex gap-1.5 items-center h-4">
                      <span className="w-2 h-2 bg-[var(--color-primary)]/60 rounded-full animate-bounce" style={{animationDelay: "0ms"}}></span>
                      <span className="w-2 h-2 bg-[var(--color-primary)]/60 rounded-full animate-bounce" style={{animationDelay: "150ms"}}></span>
                      <span className="w-2 h-2 bg-[var(--color-primary)]/60 rounded-full animate-bounce" style={{animationDelay: "300ms"}}></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={endOfMessagesRef} />
            </div>

            <div className="p-4 border-t border-[var(--color-border)] bg-[var(--color-surface)] shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]">
              <div className="relative flex items-center">
                <textarea 
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ask a question..."
                  rows={1}
                  className="w-full bg-[var(--color-surface-hover)] border border-[var(--color-border)] rounded-2xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] resize-none"
                />
                <button 
                  onClick={() => handleSend()}
                  disabled={!input.trim() || isLoading}
                  className="absolute right-2 w-8 h-8 flex items-center justify-center bg-[var(--color-primary)] text-white rounded-xl disabled:opacity-50 hover:bg-indigo-600 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
