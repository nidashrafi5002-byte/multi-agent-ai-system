import React, { createContext, useContext, useMemo, useState } from 'react';

interface Toast { id: number; message: string; tone: 'success' | 'error'; }
interface ToastContextValue { notify: (message: string, tone?: Toast['tone']) => void; }
const ToastContext = createContext<ToastContextValue>({ notify: () => undefined });

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const value = useMemo(() => ({ notify(message: string, tone: Toast['tone'] = 'success') {
    const id = Date.now(); setToasts((current) => [...current, { id, message, tone }]);
    window.setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), 3200);
  }}), []);
  return <ToastContext.Provider value={value}>{children}<div className="toast-stack" aria-live="polite">{toasts.map((toast) => <div className={`toast ${toast.tone}`} key={toast.id}>{toast.message}</div>)}</div></ToastContext.Provider>;
}
export const useToast = () => useContext(ToastContext);
