import React from 'react';
import Modal from './Modal';

export function DocumentModal({ documents, onClose }) {
  return (
    <Modal open={true} onClose={onClose} title="Ingested Documents">
      {documents && documents.length > 0 ? (
        <ul>
          {documents.map((doc, index) => (
            <li key={index}>{doc}</li>
          ))}
        </ul>
      ) : (
        <p>No documents have been ingested yet.</p>
      )}
    </Modal>
  );
}
