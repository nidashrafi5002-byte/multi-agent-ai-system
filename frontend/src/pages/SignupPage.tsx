import React, { useState } from 'react';
import { Bot, UserPlus } from 'lucide-react';
import { register } from '../api/authService';
import { useToast } from '../components/ui/Toast';

export function SignupPage() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { notify } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !username || !password || !confirmPassword) {
      notify('Please fill in all fields');
      return;
    }
    if (password !== confirmPassword) {
      notify('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      notify('Password must be at least 6 characters');
      return;
    }

    setLoading(true);
    try {
      await register({ email, username, password });
      notify('Account created successfully! Please sign in.');
      window.location.href = '/login';
    } catch (error: any) {
      notify(error.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-content auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <div className="logo-mark"><Bot size={32} /></div>
          <h1>Create Account</h1>
          <p>Join MAIA Multi-Agent Intelligence</p>
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="johndoe"
              required
            />
          </div>
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
              minLength={6}
            />
          </div>
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={6}
            />
          </div>
          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Creating account...' : <><UserPlus size={18} /> Create Account</>}
          </button>
        </form>
        <div className="auth-footer">
          <p>Already have an account? <a href="/login">Sign in</a></p>
        </div>
      </div>
    </div>
  );
}
