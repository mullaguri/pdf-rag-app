import React from 'react';

export function DocumentList({ documents }) {
  if (!documents || documents.length === 0) {
    return <p>No documents have been ingested yet.</p>;
  }

  return (
    <div>
      <h2>Ingested Documents</h2>
      <ul>
        {documents.map((doc, index) => (
          <li key={index}>{doc}</li>
        ))}
      </ul>
    </div>
  );
}
