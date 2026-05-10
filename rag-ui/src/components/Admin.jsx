import React, { useState } from 'react';
import Modal from './Modal';
import { api } from '../services/api';
import './Admin.css';

const Admin = ({ user, onClose, onReset }) => {
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
      if (onReset) {
        onReset();
      }
    } catch (error) {
      setMessage('Failed to reset vector store.');
    }
    setIsLoading(false);
  };

  const handleDeletePineconeIndex = async () => {
    setIsLoading(true);
    try {
      const response = await api.deletePineconeIndex();
      if (response.index_name) {
        setMessage(`Pinecone index '${response.index_name}' deleted successfully.`);
      } else {
        setMessage(response.message);
      }
      if (onReset) {
        onReset();
      }
    } catch (error) {
      setMessage('Failed to delete Pinecone index.');
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
        <button onClick={handleDeletePineconeIndex} disabled={isLoading}>
          {isLoading ? 'Deleting...' : 'Delete Pinecone Index'}
        </button>
      </div>
      {message && <p className="admin-message">{message}</p>}
    </Modal>
  );
};

export default Admin;
