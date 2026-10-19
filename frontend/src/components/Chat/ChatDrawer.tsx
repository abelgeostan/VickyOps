import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Bot,
  User,
  ChevronDown,
  ChevronUp,
  Maximize2,
  Minimize2,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { ChatMessage } from '../../types';
import { sendChatMessage } from '../../services/api';

interface ChatDrawerProps {
  isOpen: boolean;
  onToggle: () => void;
  onSelectOperation?: (operationId: string) => void;
  onApproveOperation?: (operationId: string) => void;
  onRejectOperation?: (operationId: string) => void;
}

export const ChatDrawer: React.FC<ChatDrawerProps> = ({
  isOpen,
  onToggle,
  onSelectOperation,
  onApproveOperation,
  onRejectOperation,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      content:
        "Hello! I am **VickyOps**, your AI DevOps and server-management assistant for Ubuntu (`vicky`). Ask me to deploy updates, check containers, inspect RAM/CPU telemetry, or restart services.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickPrompts = [
    'Update VickyAI',
    'Is StanDrive healthy?',
    "Show me what's using the most RAM",
    'Restart Nextcloud',
    'Cloudflare tunnel status',
    'Are any of my services outdated?',
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  const handleSubmit = async (text?: string) => {
    const query = text || input;
    if (!query.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await sendChatMessage(query);
      const assistantMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: 'assistant',
        content: res.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        operation_id: res.operation_id,
        requires_approval: res.requires_approval,
        approval_prompt: res.approval_prompt,
        plan_title: res.plan_title,
        steps: res.steps as any,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      // If operation was created, auto focus or inform
      if (res.operation_id && onSelectOperation) {
        onSelectOperation(res.operation_id);
      }
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          sender: 'assistant',
          content: `⚠️ Error executing request: ${e.message || 'Server error'}. Controlled tools remain safe.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className={`fixed bottom-0 right-0 z-50 bg-[#161b22] border-t border-l border-slate-800 shadow-2xl transition-all duration-300 flex flex-col ${
        isExpanded
          ? 'w-full md:w-[600px] h-[88vh]'
          : 'w-full md:w-[500px] h-[520px]'
      } rounded-tl-2xl`}
    >
      {/* Drawer Header */}
      <div className="px-4 py-3 bg-[#0d1117] border-b border-slate-800/90 flex items-center justify-between rounded-tl-2xl">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white flex items-center space-x-2">
              <span>AI DevOps Copilot</span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                Ollama / Controlled
              </span>
            </h3>
          </div>
        </div>

        <div className="flex items-center space-x-1">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title={isExpanded ? 'Collapse size' : 'Expand size'}
          >
            {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
          <button
            onClick={onToggle}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
            title="Close Drawer"
          >
            <ChevronDown className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-sm">
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}
            >
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                  isUser
                    ? 'bg-cyan-600 text-white'
                    : 'bg-slate-800 border border-slate-700 text-cyan-400'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-[85%] rounded-2xl p-3.5 text-xs leading-relaxed space-y-2 ${
                  isUser
                    ? 'bg-cyan-600 text-white rounded-tr-none'
                    : 'bg-[#0d1117] border border-slate-800 text-slate-200 rounded-tl-none shadow-sm'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* If message created an operation */}
                {msg.operation_id && (
                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                    <span className="text-slate-400 font-mono">Operation: {msg.operation_id}</span>
                    <button
                      onClick={() => onSelectOperation && onSelectOperation(msg.operation_id!)}
                      className="text-cyan-400 hover:underline flex items-center space-x-1 font-semibold"
                    >
                      <span>View live activity</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                )}

                {/* If operation requires approval */}
                {msg.requires_approval && msg.operation_id && (
                  <div className="mt-2 p-2.5 rounded-xl bg-amber-950/40 border border-amber-800/50 text-amber-200 space-y-2">
                    <div className="flex items-center space-x-1.5 font-semibold text-white">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                      <span>Approval Required</span>
                    </div>
                    <div className="flex space-x-2 pt-1">
                      <button
                        onClick={() => onApproveOperation && onApproveOperation(msg.operation_id!)}
                        className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition shadow-sm"
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => onRejectOperation && onRejectOperation(msg.operation_id!)}
                        className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isLoading && (
          <div className="flex items-center space-x-2 text-xs text-slate-400">
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
            <span>VickyOps is formulating plan...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested prompts */}
      <div className="px-4 py-2 border-t border-slate-800/60 bg-[#0d1117]/50 flex items-center space-x-2 overflow-x-auto no-scrollbar">
        <Sparkles className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
        {quickPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSubmit(prompt)}
            className="text-[11px] px-2.5 py-1 rounded-full bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/60 whitespace-nowrap transition"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Composer */}
      <div className="p-3 bg-[#0d1117] border-t border-slate-800">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="flex items-center space-x-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a DevOps command or question (e.g. 'Update VickyAI', 'Restart Plex')..."
            className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="p-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 text-slate-950 font-bold transition shadow-md shadow-cyan-500/20"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
