import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import './UserDetails.css';

const UserDetails = ({ open, onClose, user }) => {

  if (!open) return null;

  return (
    <div className="user-details-overlay" onClick={onClose}>
      <div className="user-details-modal" onClick={(e) => e.stopPropagation()}>
        <div className="user-details-header">
          <h2>User Details</h2>
          <button onClick={onClose} className="close-btn">&times;</button>
        </div>
        {user ? (
          <div className="user-details-grid">
            <div className="detail-item">
              <span className="detail-label">ID:</span>
              <span className="detail-value">{user.id}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Username:</span>
              <span className="detail-value">{user.username}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Email:</span>
              <span className="detail-value">{user.email}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Full Name:</span>
              <span className="detail-value">{user.first_name} {user.last_name}</span>
            </div>
            <div className="detail-item">
              <span className="detail-label">Role:</span>
              <span className="detail-value">{user.role}</span>
            </div>

          </div>
        ) : (
          <p>Loading...</p>
        )}
      </div>
    </div>
  );
};

export default UserDetails;
