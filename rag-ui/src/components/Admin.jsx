import React, { useState } from 'react';
import Modal from './Modal';
import { api } from '../services/api';
import './Admin.css';

const Admin = ({ user, onClose }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleCleanupTokens = async () => {
    setIsLoading(true);
    try {
      const response = await api.cleanupExpiredTokens();
      setMessage(response.message);
    } catch (error) {
      setMessage('Failed to clean up tokens.');
    }
    setIsLoading(false);
  };

  const handleResetVectorStore = async () => {
    setIsLoading(true);
    try {
      const response = await api.resetVectorStore();
      setMessage(response.message);
    } catch (error) {
      setMessage('Failed to reset vector store.');
    }
    setIsLoading(false);
  };

  if (user.role !== 'admin') {
    return null;
  }

  return (
    <Modal open={true} onClose={onClose} title="Admin Controls">
      <div className="admin-actions">
        <button onClick={handleCleanupTokens} disabled={isLoading}>
          {isLoading ? 'Cleaning up...' : 'Clean Up Expired Tokens'}
        </button>
        <button onClick={handleResetVectorStore} disabled={isLoading}>
          {isLoading ? 'Resetting...' : 'Reset Vector Store'}
        </button>
      </div>
      {message && <p className="admin-message">{message}</p>}
    </Modal>
  );
};

export default Admin;
