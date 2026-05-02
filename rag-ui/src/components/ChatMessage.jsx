export function ChatMessage({ message }) {
  const isUser  = message.role === 'user';
  const isError = message.role === 'error';

  return (
    <div className={`chat-msg ${isUser ? 'chat-msg-user' : 'chat-msg-assistant'}`}>
      <div className={`chat-avatar ${isUser ? 'avatar-user' : isError ? 'avatar-error' : 'avatar-bot'}`}>
        {isUser ? 'You' : isError ? '!' : 'AI'}
      </div>
      <div className="chat-bubble-wrap">
        <div className={`chat-bubble ${isError ? 'bubble-error' : ''}`}>
          {message.text}
        </div>

        {/* ✅ Sources + Eval verdict on same row */}
        {(message.sources?.length > 0 || message.evaluation) && (
          <div className="source-row">

            {message.sources?.length > 0 && (
              <>
                <span className="source-label">Sources:</span>
                {message.sources.map((s, i) => (
                  <span key={i} className="source-chip">{s}</span>
                ))}
              </>
            )}

            {/* ✅ Eval badge - only show if evaluation was enabled */}
            {message.evaluate && message.evaluation && (
              <span className={`eval-badge ${message.evaluation.is_correct ? 'eval-correct' : 'eval-incorrect'}`}>
                {message.evaluation.is_correct ? (
                  <>
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    correct
                  </>
                ) : (
                  <>
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                    incorrect
                  </>
                )}
              </span>
            )}

          </div>
        )}
      </div>
    </div>
  );
}

export function TypingIndicator() {
  return (
    <div className="chat-msg chat-msg-assistant">
      <div className="chat-avatar avatar-bot">AI</div>
      <div className="chat-bubble typing-bubble">
        <span className="dot" /><span className="dot" /><span className="dot" />
      </div>
    </div>
  );
}