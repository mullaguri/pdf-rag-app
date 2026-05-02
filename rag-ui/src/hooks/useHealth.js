import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export function useHealth() {
  const [status, setStatus] = useState('checking'); // checking | ready | empty | offline
  const [vectorStoreReady, setVectorStoreReady] = useState(false);

  const check = useCallback(async () => {
    try {
      const data = await api.checkHealth();
      setVectorStoreReady(data.vector_store_ready);
      setStatus(data.vector_store_ready ? 'ready' : 'empty');
    } catch {
      setStatus('offline');
      setVectorStoreReady(false);
    }
  }, []);

  useEffect(() => {
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, [check]);

  return { status, vectorStoreReady, refresh: check };
}
