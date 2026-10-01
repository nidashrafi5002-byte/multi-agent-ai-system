import React from 'react';
import { Activity, BrainCircuit, CheckCircle2, Code2, ImageIcon, PlaneTakeoff, Search, TrendingUp, UserRound } from 'lucide-react';
import { AgentRecord } from '../types';

const agents: AgentRecord[] = [
  { id: 'research', name: 'Research Agent', description: 'Source synthesis and report generation', engine: 'LangGraph', accuracy: '94.8%', latency: '180ms', active: true },
  { id: 'stock', name: 'Stock Agent', description: 'Market signals and financial context', engine: 'yFinance + Groq', accuracy: '91.6%', latency: '220ms', active: true },
  { id: 'code', name: 'Code Agent', description: 'Review, debug, and auto-fix planning', engine: 'Groq + AST', accuracy: '96.2%', latency: '145ms', active: true },
  { id: 'job', name: 'Job Agent', description: 'Resume matching and application writing', engine: 'RAG + Groq', accuracy: '93.1%', latency: '192ms', active: true },
  { id: 'flight', name: 'Flight Agent', description: 'Aircraft telemetry and route intelligence', engine: 'Aviationstack', accuracy: '89.7%', latency: '260ms', active: true },
  { id: 'image', name: 'Image Agent', description: 'Prompt design and creative generation', engine: 'Pollinations AI', accuracy: '90.4%', latency: '1.8s', active: false },
  { id: 'general', name: 'General Agent', description: 'Flexible conversational reasoning', engine: 'Groq LLM', accuracy: '95.3%', latency: '120ms', active: true },
];
const icons = [BrainCircuit, TrendingUp, Code2, UserRound, PlaneTakeoff, ImageIcon, Search];

export function AgentOverview() {
  return <div className="page-content"><header className="page-header"><div><span className="eyebrow-label">System map</span><h1>Agent Flow</h1><p>How MAIA turns one prompt into coordinated specialist work.</p></div><div className="metric-badge blue"><Activity size={14} /> 7 registered agents</div></header><section className="architecture"><div className="flow-node user-node"><UserRound size={18} /><span>User prompt</span></div><div className="flow-connector"><i /><i /><i /></div><div className="flow-node orchestrator"><BrainCircuit size={22} /><div><strong>MAIA Orchestrator</strong><span>Classify · route · synthesize</span></div><span className="node-status">Active</span></div><div className="flow-connector wide"><i /><i /><i /><i /><i /></div><div className="agent-grid">{agents.map((agent, index) => { const Icon = icons[index]; return <article className="agent-card" key={agent.id}><div className="agent-card-top"><div className="agent-icon"><Icon size={18} /></div><span className={`agent-state ${agent.active ? 'active' : 'idle'}`}><i />{agent.active ? 'Active' : 'Idle'}</span></div><h3>{agent.name}</h3><p>{agent.description}</p><div className="agent-stats"><div><span>Accuracy</span><strong>{agent.accuracy}</strong></div><div><span>Latency</span><strong>{agent.latency}</strong></div></div><div className="agent-engine"><CheckCircle2 size={13} />{agent.engine}</div></article>; })}</div></section></div>;
}
