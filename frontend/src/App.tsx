import React, { useEffect, useState } from 'react';
import { Menu } from 'lucide-react';
import './App.css';
import { Sidebar } from './components/layout/Sidebar';
import { ToastProvider } from './components/ui/Toast';
import { AgentOverview } from './pages/AgentOverview';
import { ChatPage } from './pages/ChatPage';
import { FlightPage } from './pages/FlightPage';
import { HomePage } from './pages/HomePage';
import { SettingsPage } from './pages/SettingsPage';

function App() {
  const [pathname, setPathname] = useState(window.location.pathname || '/');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [initialQuery, setInitialQuery] = useState('');

  useEffect(() => {
    const onPopState = () => setPathname(window.location.pathname || '/');
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, []);

  const navigate = (path: string, query?: string) => {
    window.history.pushState({}, '', path);
    setInitialQuery(query || '');
    setPathname(path);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const page = pathname === '/chat'
    ? <ChatPage initialQuery={initialQuery} />
    : pathname === '/agents'
        ? <AgentOverview />
        : pathname === '/flights'
          ? <FlightPage />
          : pathname === '/settings'
            ? <SettingsPage />
            : pathname === '/stocks'
              ? <ChatPage initialQuery="Analyze the latest stock opportunities and market signals." />
              : <HomePage navigate={navigate} />;

  return <ToastProvider><div className="app-shell"><Sidebar pathname={pathname} navigate={navigate} mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} /><div className="app-main"><div className="mobile-topbar"><button className="icon-button" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20} /></button><span>MAIA</span></div>{page}</div>{mobileOpen && <button className="sidebar-scrim" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />}</div></ToastProvider>;
}

export default App;
