import React, { useEffect, useState } from 'react';
import { Activity, Bot, ChevronRight, Cpu, Menu, Settings, Sparkles, X } from 'lucide-react';
import { checkBackendHealth } from '../../api/chatService';

interface SidebarProps {
  pathname: string;
  navigate: (path: string) => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

const links = [
  { path: '/', label: 'Home', icon: Sparkles },
  { path: '/chat', label: 'Chat', icon: Bot },
  { path: '/agents', label: 'Agent Flow', icon: Cpu },
  { path: '/flights', label: 'Flight Tracker', icon: Activity },
  { path: '/stocks', label: 'Stock Analysis', icon: Activity },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar({ pathname, navigate, mobileOpen, onMobileClose }: SidebarProps) {
  const [backendOnline, setBackendOnline] = useState(false);
  useEffect(() => {
    if (process.env.NODE_ENV === 'test') return undefined;
    let mounted = true;
    checkBackendHealth().then((online) => mounted && setBackendOnline(online));
    const timer = window.setInterval(() => checkBackendHealth().then((online) => mounted && setBackendOnline(online)), 30000);
    return () => { mounted = false; window.clearInterval(timer); };
  }, []);

  return (
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
      <div className="sidebar-brand">
        <div className="logo-mark"><Bot size={21} /></div>
        <div><strong>MAIA</strong><span>Multi-Agent Intelligence</span></div>
        <button className="icon-button mobile-close" onClick={onMobileClose} aria-label="Close navigation"><X size={18} /></button>
      </div>
      <nav className="sidebar-nav" aria-label="Primary navigation">
        {links.map(({ path, label, icon: Icon }) => {
          const active = path === '/' ? pathname === '/' : pathname.startsWith(path);
          return <button key={path} className={`nav-link ${active ? 'active' : ''}`} onClick={() => { navigate(path); onMobileClose(); }}>
            <Icon size={17} /><span>{label}</span>{active && <ChevronRight className="nav-chevron" size={15} />}
          </button>;
        })}
      </nav>
      <div className="sidebar-footer">
        <div className="system-pill"><span className="pulse-dot" />System Online</div>
        <div className="backend-status"><span className={`status-dot ${backendOnline ? 'online' : 'offline'}`} /><span>Backend</span><strong>{backendOnline ? 'Connected' : 'Fallback mode'}</strong></div>
        <div className="sidebar-meta">MAIA Console <span>v1.0</span></div>
      </div>
    </aside>
  );
}

export function MobileMenuButton({ onClick }: { onClick: () => void }) {
  return <button className="icon-button mobile-menu" onClick={onClick} aria-label="Open navigation"><Menu size={20} /></button>;
}
