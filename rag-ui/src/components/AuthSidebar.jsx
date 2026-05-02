import { useState } from 'react';
import './AuthSidebar.css';

export default function AuthSidebar({ open, onClose, onLogin, onRegister, onForgotPassword, loading, error }) {
  const [mode, setMode] = useState('login'); // 'login', 'register', 'forgot'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  
  // Registration fields
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  const handleLogin = (e) => {
    e.preventDefault();
    onLogin(username, password);
  };

  const handleRegister = (e) => {
    e.preventDefault();
    if (password !== confirm) {
      alert('Passwords do not match');
      return;
    }
    onRegister({
      username,
      email,
      password,
      first_name: firstName,
      last_name: lastName
    });
  };

  const handleForgot = (e) => {
    e.preventDefault();
    if (email) {
      onForgotPassword(email);
    }
  };

  if (mode === 'forgot') {
    return (
      <aside className={`auth-sidebar${open ? ' open' : ''}`}>
        <div className="auth-sidebar-header">
          <h2>Reset Password</h2>
          <button className="icon-btn" onClick={onClose} title="Close">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <form className="auth-form" onSubmit={handleForgot}>
          <p className="auth-hint">Enter your email to receive a password reset link.</p>
          <label>
            Email
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoFocus />
          </label>
          {error && <div className="auth-error">{error}</div>}
          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? 'Please wait…' : 'Send Reset Link'}
          </button>
        </form>
        <div className="auth-switch">
          <button type="button" className="link-btn" onClick={() => setMode('login')}>Back to Login</button>
        </div>
      </aside>
    );
  }

  return (
    <aside className={`auth-sidebar${open ? ' open' : ''}`}>
      <div className="auth-sidebar-header">
        <h2>{mode === 'login' ? 'Login' : 'Register'}</h2>
        <button className="icon-btn" onClick={onClose} title="Close">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      
      {mode === 'login' ? (
        <form className="auth-form" onSubmit={handleLogin}>
          <label>
            Username
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} required autoFocus />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </label>
          {error && <div className="auth-error">{error}</div>}
          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? 'Please wait…' : 'Login'}
          </button>
          <button type="button" className="forgot-link" onClick={() => setMode('forgot')}>
            Forgot Password?
          </button>
        </form>
      ) : (
        <form className="auth-form" onSubmit={handleRegister}>
          <label>
            Username *
            <input type="text" value={username} onChange={e => setUsername(e.target.value)} required minLength={3} maxLength={50} autoFocus />
          </label>
          <label>
            Email *
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </label>
          <label>
            First Name *
            <input type="text" value={firstName} onChange={e => setFirstName(e.target.value)} required />
          </label>
          <label>
            Last Name *
            <input type="text" value={lastName} onChange={e => setLastName(e.target.value)} required />
          </label>

          <label>
            Password *
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} />
          </label>
          <label>
            Confirm Password *
            <input type="password" value={confirm} onChange={e => setConfirm(e.target.value)} required minLength={6} />
          </label>
          {error && <div className="auth-error">{error}</div>}
          <button className="auth-btn" type="submit" disabled={loading}>
            {loading ? 'Please wait…' : 'Register'}
          </button>
        </form>
      )}
      
      <div className="auth-switch">
        {mode === 'login' ? (
          <>
            Don't have an account?{' '}
            <button type="button" className="link-btn" onClick={() => setMode('register')}>Register</button>
          </>
        ) : (
          <>
            Already have an account?{' '}
            <button type="button" className="link-btn" onClick={() => setMode('login')}>Login</button>
          </>
        )}
      </div>
    </aside>
  );
}
