import React, { useState } from 'react';
import API_BASE from '../config';

const AdminPanel = ({ adminToken }) => {
  const [windowData, setWindowData] = useState(null);
  const [message, setMessage] = useState('');

  const fetchWindowData = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/window`, {
        headers: {
          'Authorization': `Bearer ${adminToken}`
        }
      });
      const data = await response.json();
      if (data.error) {
        setMessage('Error: ' + data.error);
      } else {
        setWindowData(data);
        setMessage('Window data loaded successfully');
      }
    } catch (error) {
      setMessage('Error fetching window data: ' + error.message);
    }
  };

  const handleWindowUpdate = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`
        },
        body: JSON.stringify(windowData)
      });
      const data = await response.json();
      if (data.error) {
        setMessage('Error: ' + data.error);
      } else {
        setMessage(data.message);
      }
    } catch (error) {
      setMessage('Error updating window: ' + error.message);
    }
  };

  return (
    <section>
      <h2>Admin Panel</h2>
      <button onClick={fetchWindowData}>Load Window Data</button>
      <button onClick={handleWindowUpdate}>Update Window</button>
      {message && <p>{message}</p>}
      {windowData && (
        <textarea
          rows="10"
          value={JSON.stringify(windowData, null, 2)}
          onChange={(e) => {
            try {
              setWindowData(JSON.parse(e.target.value));
            } catch (error) {
              console.error('Invalid JSON:', error);
            }
          }}
        />
      )}
    </section>
  );
};

export default AdminPanel;
