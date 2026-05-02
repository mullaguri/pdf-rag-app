import { useRef, useState } from 'react';

export function DropZone({ onFiles }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef();

  const handle = (e) => {
    e.preventDefault();
    setDragging(false);
    const files = e.dataTransfer?.files || e.target.files;
    if (files?.length) onFiles(files);
  };

  return (
    <div
      className={`drop-zone ${dragging ? 'drag-over' : ''}`}
      onClick={() => inputRef.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handle}
    >
      <input ref={inputRef} type="file" accept=".pdf" multiple hidden onChange={handle} />
      <div className="drop-icon">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="12" y1="18" x2="12" y2="12"/>
          <polyline points="9 15 12 12 15 15"/>
        </svg>
      </div>
      <p className="drop-title">{dragging ? 'Release to add' : 'Drop PDFs here'}</p>
      <p className="drop-sub">or click to browse</p>
    </div>
  );
}
