import React, { useState } from 'react';
import { Bot, LogIn } from 'lucide-react';
import { login } from '../api/authService';
import { useToast } from '../components/ui/Toast';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { notify } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      notify('Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const response = await login(email, password);
      localStorage.setItem('auth_token', response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
      notify('Login successful!');
      window.location.href = '/';
    } catch (error: any) {
      notify(error.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-content auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <div className="logo-mark"><Bot size={32} /></div>
          <h1>Welcome to MAIA</h1>
          <p>Multi-Agent Intelligence System</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Signing in...' : <><LogIn size={18} /> Sign In</>}
          </button>
        </form>
        <div className="auth-footer">
          <p>Don't have an account? <a href="/signup">Sign up</a></p>
        </div>
      </div>
    </div>
  );
}
