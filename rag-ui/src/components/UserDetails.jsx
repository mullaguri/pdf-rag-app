import React, { useState } from 'react';

import Modal from './Modal';

import Admin from './Admin';

import './UserDetails.css';



const UserDetails = ({ open, onClose, user, onReset }) => {

  const [showAdmin, setShowAdmin] = useState(false);



  return (

    <Modal open={open} onClose={onClose} title="User Details">

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

          {user.role === 'admin' && (

            <button onClick={() => setShowAdmin(true)}>Admin Controls</button>

          )}

        </div>

      ) : (

        <p>Loading...</p>

      )}

      {showAdmin && <Admin user={user} onClose={() => setShowAdmin(false)} onReset={onReset} />}

    </Modal>

  );

};



export default UserDetails;

