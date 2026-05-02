export function StatusBar({ status }) {
  const config = {
    checking: { label: 'Connecting…', color: 'status-checking' },
    ready:    { label: 'Ready',       color: 'status-ready'    },
    empty:    { label: 'No documents', color: 'status-empty'   },
    offline:  { label: 'Offline',     color: 'status-offline'  },
  }[status] || { label: status, color: 'status-checking' };

  return (
    <div className={`status-bar ${config.color}`}>
      <span className="status-dot" />
      <span className="status-text">{config.label}</span>
    </div>
  );
}
