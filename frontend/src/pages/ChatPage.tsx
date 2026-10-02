import React, { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown, Clipboard, MessageSquare, Send, Sparkles, Trash2, Upload, UserRound } from 'lucide-react';
import { sendChat, analyzeFile } from '../api/chatService';
import { MarkdownText } from '../components/ui/MarkdownText';
import { useToast } from '../components/ui/Toast';
import { ChatMessage, PipelineId } from '../types';
import '../response.css';

const tabs: { id: PipelineId; label: string }[] = [['auto','Auto'],['research','Research'],['stock','Stock'],['code','Code'],['job','Job'],['flight','Flight'],['image','Image'],['general','General']].map(([id, label]) => ({ id: id as PipelineId, label }));
const icons: Record<string, string> = { research: '🔬', stock: '📈', code: '💻', job: '💼', flight: '✈️', image: '🎨', general: '💬', auto: '✦' };

interface ChatPageProps { initialQuery?: string; }
export function ChatPage({ initialQuery }: ChatPageProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState(initialQuery || '');
  const [pipeline, setPipeline] = useState<PipelineId>('auto');
  const [loading, setLoading] = useState(false);
  const [openLog, setOpenLog] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [analyzingFile, setAnalyzingFile] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const feedRef = useRef<HTMLDivElement>(null);
  const { notify } = useToast();
  useEffect(() => { feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' }); }, [messages, loading]);

  const submit = async () => {
    const text = input.trim(); if (!text || loading) return;
    const user: ChatMessage = { id: `${Date.now()}-user`, role: 'user', content: text, createdAt: new Date().toISOString() };
    setMessages((current) => [...current, user]); setInput(''); setLoading(true);
    const result = await sendChat(text, pipeline);
    const assistantId = `${Date.now()}-assistant`;
    setMessages((current) => [...current, { id: assistantId, role: 'assistant', content: '', domain: result.domain, executionLog: result.execution_log, imageUrl: result.image_url, enhancedPrompt: result.enhanced_prompt, stockChart: result.stock_chart, mapHtml: result.map_html, createdAt: new Date().toISOString() }]);
    // Reveal the completed provider response progressively so long reports do
    // not arrive as one visually overwhelming block.
    for (let index = 0; index < result.output.length; index += 18) {
      const partial = result.output.slice(0, index + 18);
      setMessages((current) => current.map((message) => message.id === assistantId ? { ...message, content: partial } : message));
      await new Promise((resolve) => window.setTimeout(resolve, 12));
    }
    setLoading(false);
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setAnalyzingFile(true);
    try {
      const result = await analyzeFile(file);
      let analysisContent = '';
      
      if (result.file_type === 'image') {
        analysisContent = `## Image Analysis\n\n**File:** ${result.filename}\n**Size:** ${result.size}\n**Format:** ${result.format}\n\n![Uploaded Image](data:image/png;base64,${result.image_data})\n\nYou can ask me to analyze this image, describe it, or extract information from it.`;
      } else {
        const pagesInfo = result.pages ? ` (${result.pages} pages)` : result.paragraphs ? ` (${result.paragraphs} paragraphs)` : '';
        analysisContent = `## Document Analysis\n\n**File:** ${result.filename}\n**Type:** ${result.file_type.toUpperCase()}${pagesInfo}\n\n### Extracted Content:\n\n${result.text}\n\n---\n\nYou can now ask me to:\n- Summarize this document\n- Extract key information\n- Answer questions about the content\n- Analyze the text`;
      }
      
      const user: ChatMessage = { id: `${Date.now()}-user`, role: 'user', content: `Uploaded file: ${file.name}`, createdAt: new Date().toISOString() };
      setMessages((current) => [...current, user]);
      
      const assistantId = `${Date.now()}-assistant`;
      setMessages((current) => [...current, { id: assistantId, role: 'assistant', content: analysisContent, domain: 'general', executionLog: [{ step: 'File analyzed successfully', duration_ms: 0 }], createdAt: new Date().toISOString() }]);
      
      notify('File analyzed successfully');
    } catch (error: any) {
      notify(error.message || 'Failed to analyze file');
    } finally {
      setAnalyzingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };
  const copy = async (message: ChatMessage) => { await navigator.clipboard?.writeText(message.content); setCopied(message.id); notify('Response copied to clipboard'); window.setTimeout(() => setCopied(null), 1500); };
  return <div className="page-content chat-page">
    <header className="page-header chat-header"><div><span className="eyebrow-label">Workspace</span><h1>MAIA Chat</h1></div><div className="chat-header-actions"><span className="metric-badge success">● 92% Precision Accuracy</span><span className="metric-badge blue">✦ 7 Active Pipelines</span><button className="icon-button" onClick={() => setMessages([])} title="Clear conversation"><Trash2 size={17} /></button></div></header>
    <div className="pipeline-tabs">{tabs.map((tab) => <button key={tab.id} className={pipeline === tab.id ? 'selected' : ''} onClick={() => setPipeline(tab.id)}><span>{icons[tab.id]}</span>{tab.label}</button>)}</div>
    <div className="message-feed" ref={feedRef}>
      {messages.length === 0 && <div className="chat-empty"><div className="empty-icon"><MessageSquare size={26} /></div><h2>What should MAIA orchestrate?</h2><p>Ask a question, paste a problem, or choose a pipeline above.</p></div>}
      {messages.map((message) => <div className={`message-row ${message.role}`} key={message.id}><div className="message-avatar">{message.role === 'user' ? <UserRound size={16} /> : <Sparkles size={16} />}</div><div className="message-body">{message.role === 'assistant' && <div className="domain-badge">{icons[message.domain || 'general']} {message.domain || 'general'} agent</div>}<div className="message-card">{message.role === 'assistant' ? <MarkdownText content={message.content} /> : <p>{message.content}</p>}</div>{message.stockChart && <iframe title="Stock analysis chart" className="visual-frame" srcDoc={message.stockChart} />}{message.mapHtml && <iframe title="Flight route map" className="visual-frame" srcDoc={message.mapHtml} />}{message.imageUrl && <img className="generated-image" src={message.imageUrl} alt={message.enhancedPrompt || 'Generated by MAIA'} />}{message.role === 'assistant' && <div className="message-actions"><button onClick={() => copy(message)}>{copied === message.id ? <Check size={13} /> : <Clipboard size={13} />}{copied === message.id ? 'Copied' : 'Copy'}</button><button onClick={() => setOpenLog(openLog === message.id ? null : message.id)}><ChevronDown size={13} />Execution log</button></div>}{openLog === message.id && message.executionLog && <div className="execution-log">{message.executionLog.map((step) => <div key={step.step}><span className="log-line" /><span>{step.step}</span><strong>{step.duration_ms}ms</strong></div>)}</div>}</div></div>)}
      {loading && <div className="message-row assistant"><div className="message-avatar"><Sparkles size={16} /></div><div className="message-card typing"><i /><i /><i /></div></div>}
    </div>
    <div className="composer-wrap"><div className="composer"><Sparkles size={18} className="composer-icon" /><input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".pdf,.docx,.txt,.png,.jpg,.jpeg,.gif,.webp" style={{ display: 'none' }} /><button onClick={() => fileInputRef.current?.click()} disabled={analyzingFile || loading} className="icon-button" title="Upload file (PDF, DOCX, TXT, Image)" aria-label="Upload file"><Upload size={17} /></button><textarea rows={1} value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit(); } }} placeholder="Ask anything — press Enter to send" /><button onClick={submit} disabled={loading || !input.trim()} aria-label="Send message"><Send size={17} /></button></div><span className="composer-hint">Shift + Enter for a new line · Upload PDF, DOCX, TXT, or images · Connected to MAIA orchestration</span></div>
  </div>;
}
