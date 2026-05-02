
import { useRef, useEffect, useState, useCallback } from 'react';
import { DropZone } from './components/DropZone';
import { DocumentList } from './components/DocumentList';
import { FileCard } from './components/FileCard';
import { ChatMessage, TypingIndicator } from './components/ChatMessage';
import AuthSidebar from './components/AuthSidebar';
import UserDetails from './components/UserDetails';
import { useHealth } from './hooks/useHealth';
import { useChat } from './hooks/useChat';
import { DocumentModal } from './components/DocumentModal';
import { useUpload } from './hooks/useUpload';
import { useAuth } from './hooks/useAuth';
import { api } from './services/api';
import './App.css';

export default function App() {
  const { status, refresh } = useHealth();
  const { user, loading: authLoading, error: authError, login, register, logout, forgotPassword, isAuthenticated } = useAuth();
  const { messages, loading, sendMessage, clearMessages,
          evaluate, setEvaluate, providers, modelsByProvider,
          selectedProvider, setSelectedProvider,
          selectedModel, setSelectedModel, currentModels,
          modelParams, updateModelParam, resetModelParams } = useChat();

  const [documents, setDocuments] = useState([]);

  const fetchDocuments = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const data = await api.getDocuments();
      setDocuments(data.documents);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    }
  }, [isAuthenticated]);

  const onUploadSuccess = useCallback(() => {
    refresh();
    fetchDocuments();
  }, [refresh, fetchDocuments]);

  const { files, addFiles, removeFile, uploadAll,
          clearDone, hasPending, isUploading } = useUpload(onUploadSuccess);

  const [input, setInput] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [paramsPanelOpen, setParamsPanelOpen] = useState(true);
  const [authSidebarOpen, setAuthSidebarOpen] = useState(!isAuthenticated);
  const [userDetailsOpen, setUserDetailsOpen] = useState(false);
  const [isDarkTheme, setIsDarkTheme] = useState(true);
  const [isDocModalOpen, setIsDocModalOpen] = useState(false);

  const bottomRef = useRef();
  const textareaRef = useRef();

  useEffect(() => {
    document.documentElement.className = isDarkTheme ? 'dark-theme' : '';
  }, [isDarkTheme]);

  useEffect(() => {
    if (!isAuthenticated) {
      setAuthSidebarOpen(true);
    } else {
      fetchDocuments();
    }
  }, [isAuthenticated, fetchDocuments]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = useCallback(() => {
    const q = input.trim();
    if (!q || loading) return;
    setInput('');
    sendMessage(q);
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }, [input, loading, sendMessage]);

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const handleInput = (e) => {
    setInput(e.target.value);
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
  };

  const handleOpenUserDetails = () => {
    setUserDetailsOpen(true);
  };

  const formatName = (name) => {
    if (!name) return "";
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
  };

  const canSend = input.trim().length > 0 && !loading && status !== 'offline';
  const doneCount = files.filter(f => f.status === 'done').length;

  const appStyle = {
    '--sidebar-width': sidebarOpen ? '320px' : '0px',
    '--params-panel-width': paramsPanelOpen ? '300px' : '0px',
  };

  return (
    <div className="app-container" style={appStyle}>
      <header className="app-header">
        <div className="header-left">
          <button className={`icon-btn toggle-sidebar ${sidebarOpen ? 'open' : ''}`} onClick={() => setSidebarOpen(!sidebarOpen)} title={sidebarOpen ? "Hide PDF Panel" : "Show PDF Panel"}>
            <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M21 18H3v-2h18v2Zm0-5H3v-2h18v2Zm0-5H3V6h18v2Z"></path></svg>
          </button>
          <h1 className="app-title">PDF RAG Application</h1>


        </div>
        <div className="header-right">
          {isAuthenticated && user ? (
            <div className="user-info">
              <button className="link-btn" onClick={handleOpenUserDetails}>My details</button>
              <button className="link-btn" onClick={logout}>Logout</button>
            </div>
          ) : (
            <button className="login-btn" onClick={() => setAuthSidebarOpen(true)}>Login</button>
          )}
          <button className="icon-btn" onClick={() => setIsDarkTheme(!isDarkTheme)} title={isDarkTheme ? "Switch to Light Theme" : "Switch to Dark Theme"}>
            {isDarkTheme ? (
              <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5s5-2.24 5-5s-2.24-5-5-5M12 5c.55 0 1 .45 1 1s-.45 1-1 1s-1-.45-1-1s.45-1 1-1m-7 6c-.55 0-1-.45-1-1s.45-1 1-1s1 .45 1 1s-.45 1-1 1m13 0c-.55 0-1-.45-1-1s.45-1 1-1s1 .45 1 1s-.45 1-1 1m-7 6c-.55 0-1-.45-1-1s.45-1 1-1s1 .45 1 1s-.45 1-1 1m0-14c.55 0 1 .45 1 1s-.45 1-1 1s-1-.45-1-1s.45-1 1-1M3.55 6.45c.39-.39 1.02-.39 1.41 0s.39 1.02 0 1.41L3.55 9.28c-.39.39-1.02.39-1.41 0s-.39-1.02 0-1.41zM19.07 7.86c.39-.39 1.02-.39 1.41 0s.39 1.02 0 1.41l-1.41 1.41c-.39.39-1.02.39-1.41 0s-.39-1.02 0-1.41zm-1.41 10.62c.39.39 1.02.39 1.41 0s.39 1.02 0 1.41l-1.41 1.41c-.39.39-1.02.39-1.41 0s-.39-1.02 0-1.41zM4.96 19.07c.39.39 1.02.39 1.41 0s.39 1.02 0 1.41l-1.41 1.41c-.39.39-1.02.39-1.41 0s-.39-1.02 0-1.41z"></path></svg>
            ) : (
              <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36c-.98 1.37-2.58 2.26-4.4 2.26c-3.31 0-6-2.69-6-6c0-1.82.89-3.42 2.26-4.4A8.91 8.91 0 0 0 3 12a9 9 0 0 0 9-9"></path></svg>
            )}
          </button>
          <button className={`icon-btn toggle-params ${paramsPanelOpen ? 'open' : ''}`} onClick={() => setParamsPanelOpen(!paramsPanelOpen)} title={paramsPanelOpen ? "Hide Parameters Panel" : "Show Parameters Panel"}>
            <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M12 16a4 4 0 1 1 0-8a4 4 0 0 1 0 8m0-6a2 2 0 1 0 0 4a2 2 0 0 0 0-4m6 7.66V20h-2v-2.34c-1.12.54-2.45.84-3.86.84s-2.74-.3-3.86-.84L6 20H4v-2.34c-1.12-.54-2-1.5-2-2.66V10c0-1.16.88-2.12 2-2.66V5h2v2.34c1.12-.54 2.45-.84 3.86-.84s2.74.3 3.86.84L18 5h2v2.34c1.12.54 2 1.5 2 2.66v5c0 1.16-.88 2.12-2 2.66M18 10v5a2 2 0 0 0-1-1.73V10.7a2 2 0 0 0 1-1.73V10M6 10v5c-.53.25-1 .7-1 1.27V10.7a2.001 2.001 0 0 0 1-1.73V10Z"></path></svg>
          </button>
        </div>
      </header>

      <AuthSidebar
        open={authSidebarOpen}
        onClose={() => setAuthSidebarOpen(false)}
        onLogin={async (username, password) => {
          const ok = await login(username, password);
          if (ok) setAuthSidebarOpen(false);
        }}
        onRegister={async (userData) => {
          const ok = await register(userData);
          if (ok) setAuthSidebarOpen(false);
        }}
        onForgotPassword={async (email) => {
          // Placeholder for forgot password logic
        }}
        loading={authLoading}
        error={authError}
      />

      <UserDetails open={userDetailsOpen} onClose={() => setUserDetailsOpen(false)} user={user} />

      <div className="main-content">
        {/* Left Sidebar (PDF Upload) */}
        <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
          <div className="sidebar-header">
            <div className="sidebar-logo">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
              <span>PDF Upload</span>
            </div>
          </div>

          <div className="sidebar-body">
            <DropZone onFiles={addFiles} />
            {files.length > 0 && (
              <div className="file-list">
                <div className="file-list-header">
                  <span>{files.length} file{files.length !== 1 ? 's' : ''}</span>
                  {doneCount > 0 && <button className="link-btn" onClick={clearDone}>Clear indexed</button>}
                </div>
                {files.map(f => <FileCard key={f.id} file={f} onRemove={removeFile} />)}
              </div>
            )}
          </div>
          <div className="sidebar-footer">
            <button className="upload-btn" disabled={!hasPending || isUploading} onClick={uploadAll}>
              {isUploading ? (
                <><span className="spinner" /> Indexing...</>
              ) : (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>
                    <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>
                  </svg>
                  Index {files.filter(f => f.status === 'pending' || f.status === 'error').length} PDF{files.filter(f => f.status === 'pending' || f.status === 'error').length !== 1 ? 's' : ''}
                </>
              )}
            </button>
            <div className="ingested-docs-link">
              <button className="link-btn" onClick={() => setIsDocModalOpen(true)}>Show ingested documents</button>
            </div>
          </div>
        </aside>

        {/* Main Chat Area */}
        <main className="chat-main">
          <header className="chat-header">
            <div className="chat-header-left">
              {isAuthenticated && user && (
                <>
                  <div className="user-info">
                    <span>Welcome <strong>{formatName(user.first_name)} {formatName(user.last_name)}</strong></span>
                  </div>
                  <div className={`server-status ${isAuthenticated ? 'online' : 'offline'}`}>
                    <span className="status-indicator" title={`Server is ${isAuthenticated ? 'online' : 'offline'}`}></span>
                  </div>
                </>
              )}
            </div>
            <div className="chat-header-right">
              {messages.length > 0 && (
                <button className="icon-btn" onClick={clearMessages} title="Clear chat">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                    <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
                  </svg>
                </button>
              )}
            </div>
          </header>

          <div className="chat-messages">
            {messages.length === 0 && !loading && (
              <div className="empty-chat">
                <div className="empty-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                  </svg>
                </div>
                <p className="empty-title">Ready to answer</p>
                <p className="empty-sub">Index your PDFs on the left, then ask anything about them.</p>
                <div className="suggestion-row">
                  {['Summarize the document', 'What are the key findings?', 'List the main topics covered'].map(s => (
                    <button key={s} className="suggestion-chip" onClick={() => { setInput(s); textareaRef.current?.focus(); }}>{s}</button>
                  ))}
                </div>
              </div>
            )}
            {messages.map(msg => <ChatMessage key={msg.id} message={msg} />)}
            {loading && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>

          <div className="chat-input-area">
            <div className="input-box">
                <div className="input-main-row">
                  <textarea
                    ref={textareaRef}
                    className="chat-textarea"
                    placeholder={status === 'offline' ? 'Server offline...' : 'Ask a question about your documents...'}
                    value={input}
                    onChange={handleInput}
                    onKeyDown={handleKey}
                    rows={1}
                    disabled={status === 'offline'}
                  />
                  <button className="send-btn" disabled={!canSend} onClick={handleSend}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="17 11 12 6 7 11"></polyline>
                      <line x1="12" y1="18" x2="12" y2="6"></line>
                    </svg>
                  </button>
                </div>
                <div className="input-options">
                  <button
                    className={`eval-toggle ${evaluate ? 'eval-on' : 'eval-off'}`}
                    onClick={() => setEvaluate(e => !e)}
                    title={evaluate ? 'Evaluation on — click to disable' : 'Evaluation off — click to enable'}
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="9 11 12 14 22 4"/>
                      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
                    </svg>
                    <span>Eval</span>
                  </button>
                  {providers.length > 0 && (
                    <div className="input-model-selects">
                      <select
                        className="input-provider-select"
                        value={selectedProvider}
                        onChange={(e) => setSelectedProvider(e.target.value)}
                        title="Select provider"
                      >
                        {providers.map(p => (
                          <option key={p} value={p}>{p}</option>
                        ))}
                      </select>
                      <select
                        className="input-model-select"
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        title="Select model"
                        disabled={!selectedProvider}
                      >
                        <option value="">Model</option>
                        {currentModels.map(m => (
                          <option key={m.model} value={m.model}>
                            {m.model.split(':')[1] || m.model}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              </div>
              <p className="input-hint">Enter to send · Shift+Enter for new line · {evaluate ? '✓ Evaluation enabled' : '○ Evaluation disabled'}</p>
          </div>
        </main>

        {/* Right Sidebar (Model Parameters) */}
        <aside className={`params-panel ${paramsPanelOpen ? 'open' : 'closed'}`}>
          <div className="params-panel-header">
            <h3>Model Parameters</h3>
          </div>
          <div className="params-panel-body">
            <div className="param-group">
              <label htmlFor="param-temperature">Temperature</label>
              <input
                id="param-temperature"
                type="number"
                min="0"
                max="2"
                step="0.1"
                value={modelParams.temperature ?? ''}
                onChange={(e) => updateModelParam('temperature', parseFloat(e.target.value) || null)}
                placeholder="0.7"
              />
              <span className="param-hint">0-2 (higher = more creative)</span>
            </div>
            <div className="param-group">
              <label htmlFor="param-top_p">Top P</label>
              <input
                id="param-top_p"
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={modelParams.top_p ?? ''}
                onChange={(e) => updateModelParam('top_p', parseFloat(e.target.value) || null)}
                placeholder="1.0"
              />
              <span className="param-hint">0-1 (nucleus sampling)</span>
            </div>
            <div className="param-group">
              <label htmlFor="param-top_k">Top K</label>
              <input
                id="param-top_k"
                type="number"
                min="0"
                max="100"
                step="1"
                value={modelParams.top_k ?? ''}
                onChange={(e) => updateModelParam('top_k', parseInt(e.target.value) || null)}
                placeholder="50"
              />
              <span className="param-hint">0-100 (vocab sampling)</span>
            </div>
            <div className="param-group">
              <label htmlFor="param-max_tokens">Max Tokens</label>
              <input
                id="param-max_tokens"
                type="number"
                min="1"
                max="32000"
                step="1"
                value={modelParams.max_tokens ?? ''}
                onChange={(e) => updateModelParam('max_tokens', parseInt(e.target.value) || null)}
                placeholder="No limit"
              />
              <span className="param-hint">1-32000 (leave empty for default)</span>
            </div>
            <div className="param-group">
              <label htmlFor="param-seed">Seed</label>
              <input
                id="param-seed"
                type="number"
                step="1"
                value={modelParams.seed ?? ''}
                onChange={(e) => updateModelParam('seed', e.target.value === '' ? null : parseInt(e.target.value))}
                placeholder="Random"
              />
              <span className="param-hint">Integer for reproducibility</span>
            </div>
          </div>
          <div className="params-panel-footer">
            <button className="reset-params-btn" onClick={resetModelParams}>
              Reset to Defaults
            </button>
          </div>
        </aside>
      </div>
      {isDocModalOpen && <DocumentModal documents={documents} onClose={() => setIsDocModalOpen(false)} />}
    </div>
  );
}
