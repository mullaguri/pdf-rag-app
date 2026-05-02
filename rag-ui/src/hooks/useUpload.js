import { useState, useCallback } from 'react';
import { api } from '../services/api';

export function useUpload(onSuccess) {
  const [files, setFiles] = useState([]);

  const addFiles = useCallback((incoming) => {
    const pdfs = Array.from(incoming).filter(f => f.name.endsWith('.pdf'));
    setFiles(prev => {
      const existing = new Set(prev.map(f => f.name));
      const fresh = pdfs.filter(f => !existing.has(f.name)).map(f => ({
        id: `${f.name}-${f.size}`,
        file: f,
        name: f.name,
        size: f.size,
        status: 'pending',
        progress: 0,
        error: null,
        chunks: null,
        pages: null,
      }));
      return [...prev, ...fresh];
    });
  }, []);

  const removeFile = useCallback((id) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  }, []);

  const uploadAll = useCallback(async () => {
    const pending = files.filter(f => f.status === 'pending' || f.status === 'error');
    for (const file of pending) {
      setFiles(prev => prev.map(f => f.id === file.id ? { ...f, status: 'uploading', progress: 0 } : f));
      try {
        const result = await api.uploadPdf(file.file, (progress) => {
          setFiles(prev => prev.map(f => f.id === file.id ? { ...f, progress } : f));
        });
        setFiles(prev => prev.map(f =>
          f.id === file.id
            ? { ...f, status: 'done', progress: 100, chunks: result.chunks, pages: result.pages }
            : f
        ));
        if (onSuccess) onSuccess();
      } catch (err) {
        setFiles(prev => prev.map(f =>
          f.id === file.id ? { ...f, status: 'error', error: err.message } : f
        ));
      }
    }
  }, [files, onSuccess]);

  const clearDone = useCallback(() => {
    setFiles(prev => prev.filter(f => f.status !== 'done'));
  }, []);

  const hasPending = files.some(f => f.status === 'pending' || f.status === 'error');
  const isUploading = files.some(f => f.status === 'uploading');

  return { files, addFiles, removeFile, uploadAll, clearDone, hasPending, isUploading };
}
