import React, { useState } from 'react';
import { ArrowRight, BrainCircuit, Code2, PlaneTakeoff, Search, Sparkles, TrendingUp } from 'lucide-react';

interface HomePageProps { navigate: (path: string, query?: string) => void; }

const features = [
  { title: 'Research & Reports', eyebrow: 'LangGraph', icon: BrainCircuit, color: 'blue', copy: 'Synthesize sources into clear, source-backed briefings for decisions that move quickly.' },
  { title: 'Stock Analysis', eyebrow: 'Live Charts', icon: TrendingUp, color: 'green', copy: 'Read catalysts, sentiment, and market context through a focused analyst workflow.' },
  { title: 'Code Review & Auto-Fix', eyebrow: 'Engineering', icon: Code2, color: 'amber', copy: 'Find security risks and edge cases, then turn findings into a practical fix plan.' },
  { title: 'Real-Time Flight Tracking', eyebrow: 'Telemetry', icon: PlaneTakeoff, color: 'cyan', copy: 'Track aircraft, route progress, and operational status on an interactive live map.' },
];
const examples = ['Analyze AAPL Q3 earnings', 'Review auth.py for security vulnerabilities', 'Track flight AA123', 'Write executive summary on quantum computing'];

export function HomePage({ navigate }: HomePageProps) {
  const [query, setQuery] = useState('');
  const submit = () => { if (query.trim()) navigate('/chat', query.trim()); };
  return <div className="page-content home-page">
    <section className="hero-panel">
      <div className="mesh-glow mesh-one" /><div className="mesh-glow mesh-two" />
      <div className="hero-copy"><div className="eyebrow"><Sparkles size={14} /> Intelligent work, orchestrated</div><h1>Welcome to <span>MAIA</span></h1><p>Your Multi-Agent Intelligence System</p><small>One workspace for research, analysis, creation, and action. Route a task to the right specialist or let MAIA choose for you.</small></div>
      <div className="prompt-shell"><Search size={19} /><input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && submit()} placeholder="Ask MAIA anything..." aria-label="Ask MAIA anything" /><button onClick={submit} aria-label="Send prompt"><ArrowRight size={19} /></button></div>
      <div className="example-row"><span>Try:</span>{examples.map((example) => <button key={example} onClick={() => setQuery(example)}>{example}</button>)}</div>
    </section>
    <div className="section-heading"><div><span className="eyebrow-label">Specialist pipelines</span><h2>Launch an agent</h2></div><button className="text-button" onClick={() => navigate('/agents')}>View architecture <ArrowRight size={15} /></button></div>
    <section className="feature-grid">{features.map(({ title, eyebrow, icon: Icon, color, copy }) => <article className="feature-card" key={title}><div className={`feature-icon ${color}`}><Icon size={22} /></div><span className="card-eyebrow">{eyebrow}</span><h3>{title}</h3><p>{copy}</p><button onClick={() => navigate('/chat', title)} className="launch-button">Launch agent <ArrowRight size={15} /></button></article>)}</section>
  </div>;
}
