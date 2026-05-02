export function FileCard({ file, onRemove }) {
  const fmt = (b) => b < 1048576 ? `${Math.round(b / 1024)} KB` : `${(b / 1048576).toFixed(1)} MB`;

  const statusLabel = {
    pending: 'Pending',
    uploading: `${file.progress}%`,
    done: 'Indexed',
    error: 'Failed',
  }[file.status];

  return (
    <div className={`file-card file-${file.status}`}>
      <div className="file-card-icon">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
      </div>
      <div className="file-card-body">
        <span className="file-card-name" title={file.name}>{file.name}</span>
        <span className="file-card-meta">
          {fmt(file.size)}
          {file.pages && ` · ${file.pages}p`}
          {file.chunks && ` · ${file.chunks} chunks`}
        </span>
        {file.status === 'uploading' && (
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${file.progress}%` }} />
          </div>
        )}
        {file.error && <span className="file-error">{file.error}</span>}
      </div>
      <div className="file-card-right">
        <span className={`badge badge-${file.status}`}>{statusLabel}</span>
        {file.status !== 'uploading' && (
          <button className="remove-btn" onClick={() => onRemove(file.id)} title="Remove">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
