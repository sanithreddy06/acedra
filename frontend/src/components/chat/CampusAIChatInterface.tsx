import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Bot,
  User as UserIcon,
  Send,
  Plus,
  Trash2,
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  BookOpen,
  FileText,
  ShieldCheck,
  ShieldAlert,
  HelpCircle,
  ExternalLink,
  ChevronRight,
  Info,
  Clock,
  Code,
  GraduationCap,
  Briefcase,
  AlertTriangle,
  Lock,
  Layers,
  Search
} from 'lucide-react';
import { api } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';

export const CampusAIChatInterface: React.FC = () => {
  const { user } = useAuth();
  const isAuthenticated = !!user;

  // Assistant Mode: Mode A (Public) or Mode B (Personal)
  const [activeMode, setActiveMode] = useState<'PUBLIC_MODE_A' | 'PERSONAL_MODE_B'>('PUBLIC_MODE_A');
  const [conversations, setConversations] = useState<any[]>([]);
  const [currentConversation, setCurrentConversation] = useState<any | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [inputText, setInputText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [suggestedQuestions, setSuggestedQuestions] = useState<any[]>([]);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const [feedbackSent, setFeedbackSent] = useState<Record<number, boolean>>({});
  const [selectedCitation, setSelectedCitation] = useState<any | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate or retrieve persistent anonymous session ID for public chats
  const [sessionId] = useState<string>(() => {
    let sid = localStorage.getItem('campus_ai_session_id');
    if (!sid) {
      sid = 'session_' + Math.random().toString(36).substring(2, 12);
      localStorage.setItem('campus_ai_session_id', sid);
    }
    return sid;
  });

  // Load conversations
  const loadConversations = async () => {
    try {
      const data = await api.getAIConversations(sessionId);
      setConversations(data);
      // Select first conversation or null
      if (data.length > 0 && !currentConversation) {
        selectConversation(data[0].id);
      }
    } catch (err) {
      console.error('Failed to load conversations', err);
    }
  };

  // Load suggested questions
  const loadSuggestedQuestions = async (mode: string) => {
    try {
      const questions = await api.getSuggestedQuestions(mode);
      setSuggestedQuestions(questions);
    } catch (err) {
      console.error('Failed to load suggested questions', err);
    }
  };

  useEffect(() => {
    loadConversations();
    loadSuggestedQuestions(activeMode);
  }, [activeMode]);

  // Select conversation and load its messages
  const selectConversation = async (convId: number) => {
    try {
      const detail = await api.getAIConversation(convId);
      setCurrentConversation(detail);
      setMessages(detail.messages || []);
      setActiveMode(detail.mode as any);
      setTimeout(scrollToBottom, 100);
    } catch (err) {
      console.error('Failed to load conversation details', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Start new conversation
  const handleStartNewConversation = async (modeToStart: 'PUBLIC_MODE_A' | 'PERSONAL_MODE_B' = activeMode) => {
    if (modeToStart === 'PERSONAL_MODE_B' && !isAuthenticated) {
      alert('Please sign in with student credentials to access your personal AI assistant.');
      return;
    }
    try {
      setIsLoading(true);
      const newConv = await api.createAIConversation({
        mode: modeToStart,
        title: modeToStart === 'PERSONAL_MODE_B' ? 'Personal Student Assistant' : 'Campus Knowledge Assistant',
        session_id: sessionId,
      });
      setConversations([newConv, ...conversations]);
      setCurrentConversation(newConv);
      setMessages([]);
      setActiveMode(modeToStart);
      loadSuggestedQuestions(modeToStart);
    } catch (err: any) {
      alert(err.message || 'Failed to start conversation');
    } finally {
      setIsLoading(false);
    }
  };

  // Delete conversation
  const handleDeleteConversation = async (e: React.MouseEvent, convId: number) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this conversation?')) return;
    try {
      await api.deleteAIConversation(convId);
      const filtered = conversations.filter(c => c.id !== convId);
      setConversations(filtered);
      if (currentConversation?.id === convId) {
        if (filtered.length > 0) {
          selectConversation(filtered[0].id);
        } else {
          setCurrentConversation(null);
          setMessages([]);
        }
      }
    } catch (err: any) {
      alert(err.message || 'Failed to delete conversation');
    }
  };

  // Send message
  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputText).trim();
    if (!query || isLoading) return;

    // Check Mode B auth guard
    if (activeMode === 'PERSONAL_MODE_B' && !isAuthenticated) {
      alert('Mode B requires authentication. Please sign in to query personal student records.');
      return;
    }

    let activeConvId = currentConversation?.id;

    // Create conversation on the fly if none active
    if (!activeConvId) {
      try {
        const newConv = await api.createAIConversation({
          mode: activeMode,
          title: query.substring(0, 40),
          session_id: sessionId,
        });
        activeConvId = newConv.id;
        setCurrentConversation(newConv);
        setConversations([newConv, ...conversations]);
      } catch (err: any) {
        alert(err.message || 'Could not initiate session');
        return;
      }
    }

    // Add user message to UI immediately
    const tempUserMsg = {
      id: Date.now(),
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
      sources_json: [],
    };
    setMessages(prev => [...prev, tempUserMsg]);
    setInputText('');
    setIsLoading(true);
    setTimeout(scrollToBottom, 50);

    try {
      const assistantMsg = await api.sendAIMessage(activeConvId, query, user?.student_id);
      setMessages(prev => [...prev, assistantMsg]);
      // Refresh conversation list to update title
      loadConversations();
    } catch (err: any) {
      const errorMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `**Error**: ${err.message || 'Unable to complete request. Please try again.'}`,
        created_at: new Date().toISOString(),
        sources_json: [],
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
      setTimeout(scrollToBottom, 100);
    }
  };

  const handleCopy = (text: string, msgId: number) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleFeedback = async (msgId: number, isHelpful: boolean) => {
    try {
      await api.submitMessageFeedback(msgId, isHelpful);
      setFeedbackSent(prev => ({ ...prev, [msgId]: isHelpful }));
    } catch (err) {
      console.error('Failed to submit feedback', err);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Header Card */}
      <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-gradient-to-tr from-blue-600 to-indigo-600 rounded-xl text-white shadow-md shadow-blue-500/20">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Smart Campus Conversational AI
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300">
                  RAG Grounded
                </span>
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Dual-mode institutional intelligence: Public University Guide & Authenticated Student Companion
              </p>
            </div>
          </div>
        </div>

        {/* Dual Mode Switcher */}
        <div className="flex items-center p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl border border-slate-200 dark:border-slate-700">
          <button
            onClick={() => {
              setActiveMode('PUBLIC_MODE_A');
              handleStartNewConversation('PUBLIC_MODE_A');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeMode === 'PUBLIC_MODE_A'
                ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5" />
            Mode A: Public Assistant
          </button>

          <button
            onClick={() => {
              if (!isAuthenticated) {
                alert('Mode B requires authentication. Sign in with student credentials to unlock your personal assistant.');
                return;
              }
              setActiveMode('PERSONAL_MODE_B');
              handleStartNewConversation('PERSONAL_MODE_B');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              activeMode === 'PERSONAL_MODE_B'
                ? 'bg-white dark:bg-slate-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            {isAuthenticated ? (
              <GraduationCap className="w-3.5 h-3.5" />
            ) : (
              <Lock className="w-3.5 h-3.5 text-amber-500" />
            )}
            Mode B: Personal Student
          </button>
        </div>
      </div>

      {/* Main Dual-Pane Chat Area */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[720px]">
        {/* Left Drawer: Conversation History */}
        <div className="lg:col-span-1 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-4 flex flex-col shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5" />
              Conversations
            </span>
            <button
              onClick={() => handleStartNewConversation(activeMode)}
              className="p-1.5 bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 transition flex items-center gap-1 text-[11px] font-semibold"
              title="New Conversation"
            >
              <Plus className="w-3.5 h-3.5" />
              New
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
            {conversations.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-xs">
                No conversation history yet. Start a chat!
              </div>
            ) : (
              conversations.map(conv => {
                const isSelected = currentConversation?.id === conv.id;
                return (
                  <div
                    key={conv.id}
                    onClick={() => selectConversation(conv.id)}
                    className={`p-2.5 rounded-xl text-left cursor-pointer transition-all border group flex items-start justify-between gap-2 ${
                      isSelected
                        ? 'bg-blue-50/70 dark:bg-blue-950/40 border-blue-200 dark:border-blue-900 text-blue-900 dark:text-blue-100'
                        : 'border-transparent hover:bg-slate-50 dark:hover:bg-slate-800/60 text-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <div className="overflow-hidden">
                      <div className="flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${conv.mode === 'PERSONAL_MODE_B' ? 'bg-indigo-500' : 'bg-emerald-500'}`} />
                        <h4 className="text-xs font-semibold truncate">{conv.title || 'Conversation'}</h4>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5 truncate">
                        {conv.mode === 'PERSONAL_MODE_B' ? 'Personal Companion' : 'Public Knowledge'} &bull; {conv.messages_count || 0} msgs
                      </p>
                    </div>

                    <button
                      onClick={(e) => handleDeleteConversation(e, conv.id)}
                      className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-500 transition p-1"
                      title="Delete conversation"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                );
              })
            )}
          </div>

          {/* Assistant Security Pill Footer */}
          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center gap-2 text-[10px] text-slate-500">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            <span>AI Safety Filter & Prompt-Injection Guard Active</span>
          </div>
        </div>

        {/* Right Main Chat Column */}
        <div className="lg:col-span-3 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col shadow-sm overflow-hidden">
          {/* Chat Stream Header */}
          <div className="px-5 py-3.5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className={`p-1.5 rounded-lg text-white ${activeMode === 'PERSONAL_MODE_B' ? 'bg-indigo-600' : 'bg-blue-600'}`}>
                {activeMode === 'PERSONAL_MODE_B' ? <GraduationCap className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>
              <div>
                <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                  {activeMode === 'PERSONAL_MODE_B' ? 'Student Intelligence & Academic Companion' : 'Campus Knowledge & General Education Guide'}
                </h3>
                <span className="text-[10px] text-slate-400 flex items-center gap-1">
                  {activeMode === 'PERSONAL_MODE_B' ? (
                    <>
                      <Lock className="w-2.5 h-2.5 text-emerald-500" />
                      Role-Authorized Personal Context: {user?.full_name || 'Student'} ({user?.email})
                    </>
                  ) : (
                    <>
                      <BookOpen className="w-2.5 h-2.5 text-blue-500" />
                      Public Educational Knowledge & Official University Documents
                    </>
                  )}
                </span>
              </div>
            </div>

            <div className="text-[11px] font-semibold text-slate-400">
              {messages.length} message{messages.length !== 1 ? 's' : ''}
            </div>
          </div>

          {/* Messages Feed Area */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto py-8">
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-3 ${activeMode === 'PERSONAL_MODE_B' ? 'bg-indigo-100 dark:bg-indigo-950 text-indigo-600' : 'bg-blue-100 dark:bg-blue-950 text-blue-600'}`}>
                  <Sparkles className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  {activeMode === 'PERSONAL_MODE_B' ? 'How can I assist your academic journey today?' : 'Ask anything about REVA University or Academics'}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 mb-6">
                  {activeMode === 'PERSONAL_MODE_B'
                    ? 'Get instant answers about your attendance percentage, CGPA, CIA marks, risk alerts, skill gap profile, and personalized study plans.'
                    : 'Explore approved university policies on attendance, exam rules, placements, internships, or ask general programming questions.'}
                </p>

                {/* Suggested Questions Grid */}
                <div className="w-full text-left space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                    Suggested Exploration Prompts:
                  </span>
                  {suggestedQuestions.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendMessage(q.prompt)}
                      className="w-full p-2.5 text-left rounded-xl bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300 transition flex items-center justify-between group"
                    >
                      <span className="truncate pr-2">{q.prompt}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-500 transition shrink-0" />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map(msg => {
                const isUser = msg.role === 'user';
                return (
                  <div
                    key={msg.id}
                    className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
                  >
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold ${
                        isUser
                          ? 'bg-blue-600 text-white'
                          : activeMode === 'PERSONAL_MODE_B'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-800 text-white'
                      }`}
                    >
                      {isUser ? <UserIcon className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                    </div>

                    <div className={`max-w-[85%] space-y-2 ${isUser ? 'items-end' : 'items-start'}`}>
                      <div
                        className={`p-4 rounded-2xl text-xs leading-relaxed ${
                          isUser
                            ? 'bg-blue-600 text-white rounded-tr-none'
                            : 'bg-slate-50 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100 rounded-tl-none shadow-sm'
                        }`}
                      >
                        {/* Message body with Markdown representation */}
                        <div className="prose prose-xs dark:prose-invert max-w-none whitespace-pre-line font-sans">
                          {msg.content}
                        </div>
                      </div>

                      {/* Assistant Citations & Action Tools */}
                      {!isUser && (
                        <div className="space-y-2">
                          {/* Grounded Citation Pills */}
                          {msg.sources_json && msg.sources_json.length > 0 && (
                            <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200 dark:border-slate-800 space-y-1.5">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1">
                                <BookOpen className="w-3 h-3 text-blue-500" />
                                Verified Institutional Citations ({msg.sources_json.length})
                              </span>
                              <div className="flex flex-wrap gap-1.5">
                                {msg.sources_json.map((cit: any, idx: number) => (
                                  <button
                                    key={idx}
                                    onClick={() => setSelectedCitation(cit)}
                                    className="px-2 py-1 rounded-lg text-[10px] font-medium bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 hover:border-blue-500 text-slate-700 dark:text-slate-300 flex items-center gap-1 transition"
                                    title="Click to view citation excerpt"
                                  >
                                    <FileText className="w-2.5 h-2.5 text-blue-500" />
                                    <span className="truncate max-w-[200px]">{cit.document_title}</span>
                                    <span className="text-slate-400">({cit.section})</span>
                                    <span className="px-1 py-0.2 rounded bg-blue-50 dark:bg-blue-950 text-blue-600 text-[9px] font-mono">
                                      {Math.round(cit.relevance_score * 100)}%
                                    </span>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Action Footer: Copy, Helpful/Unhelpful Feedback */}
                          <div className="flex items-center gap-3 text-[10px] text-slate-400 pt-0.5">
                            <button
                              onClick={() => handleCopy(msg.content, msg.id)}
                              className="hover:text-slate-600 dark:hover:text-slate-200 flex items-center gap-1 transition"
                            >
                              {copiedId === msg.id ? (
                                <>
                                  <Check className="w-3 h-3 text-emerald-500" />
                                  <span className="text-emerald-500">Copied</span>
                                </>
                              ) : (
                                <>
                                  <Copy className="w-3 h-3" />
                                  <span>Copy</span>
                                </>
                              )}
                            </button>

                            <span>&bull;</span>

                            <div className="flex items-center gap-1.5">
                              <span>Was this helpful?</span>
                              <button
                                onClick={() => handleFeedback(msg.id, true)}
                                className={`p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition ${
                                  feedbackSent[msg.id] === true ? 'text-emerald-500 font-bold' : ''
                                }`}
                                title="Helpful"
                              >
                                <ThumbsUp className="w-3 h-3" />
                              </button>
                              <button
                                onClick={() => handleFeedback(msg.id, false)}
                                className={`p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition ${
                                  feedbackSent[msg.id] === false ? 'text-rose-500 font-bold' : ''
                                }`}
                                title="Not helpful"
                              >
                                <ThumbsDown className="w-3 h-3" />
                              </button>
                            </div>

                            {msg.processing_time_ms ? (
                              <>
                                <span>&bull;</span>
                                <span>{msg.processing_time_ms} ms</span>
                              </>
                            ) : null}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}

            {isLoading && (
              <div className="flex items-center gap-2 text-xs text-slate-400 p-2">
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                <span>Generating grounded intelligence response...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar Area */}
          <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder={
                  activeMode === 'PERSONAL_MODE_B'
                    ? 'Ask about your attendance, CGPA, CIA tests, skill gaps, or request a study plan...'
                    : 'Ask about attendance rules, exam policies, placements, code, or interview advice...'
                }
                disabled={isLoading}
                className="flex-1 px-4 py-2.5 text-xs rounded-xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
              />
              <button
                type="submit"
                disabled={!inputText.trim() || isLoading}
                className={`p-2.5 rounded-xl text-white font-semibold transition disabled:opacity-40 shadow-sm ${
                  activeMode === 'PERSONAL_MODE_B' ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Citation Preview Modal */}
      {selectedCitation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 max-w-lg w-full space-y-4 shadow-xl">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                  {selectedCitation.category || 'Official Document'}
                </span>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
                  {selectedCitation.document_title}
                </h3>
                <p className="text-xs text-slate-400">
                  {selectedCitation.section} &bull; Page {selectedCitation.page}
                </p>
              </div>
              <button
                onClick={() => setSelectedCitation(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1"
              >
                &times;
              </button>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-200 leading-relaxed font-mono whitespace-pre-wrap">
              {selectedCitation.snippet}
            </div>

            <div className="flex items-center justify-between text-xs pt-2">
              <span className="text-slate-400">
                Vector Relevance: <strong className="text-blue-600">{Math.round(selectedCitation.relevance_score * 100)}%</strong>
              </span>
              <button
                onClick={() => setSelectedCitation(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-xs font-semibold text-slate-700 dark:text-slate-300 transition"
              >
                Close Excerpt
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
