import React, { useState } from 'react';
import API_BASE from '../config';

const WINDOW_SHAPE = [30, 5];
const FEATURE_NAMES = ['pressure', 'dew_point_f', 'humidity', 'wind_speed', 'temp_f'];

/**
 * Admin panel — view and edit the rolling 30×5 prediction window.
 * Only rendered when the admin token has been verified in App.js.
 */
const AdminPanel = ({ adminToken }) => {
  const [windowData, setWindowData] = useState(null);
  const [rawText, setRawText] = useState('');
  const [jsonError, setJsonError] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const authHeaders = {
    Authorization: `Bearer ${adminToken}`,
    'Content-Type': 'application/json',
  };

  const fetchWindowData = async () => {
    setLoading(true);
    setMessage('');
    try {
      const response = await fetch(`${API_BASE}/api/admin/window`, {
        headers: authHeaders,
      });
      const data = await response.json();
      if (data.error) {
        setMessage('Error: ' + data.error);
      } else {
        setWindowData(data);
        setRawText(JSON.stringify(data, null, 2));
        setJsonError('');
        setMessage('Window data loaded successfully.');
      }
    } catch (err) {
      setMessage('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTextChange = (e) => {
    const text = e.target.value;
    setRawText(text);
    try {
      const parsed = JSON.parse(text);
      // Basic shape validation before sending
      if (
        !Array.isArray(parsed) ||
        parsed.length !== WINDOW_SHAPE[0] ||
        !parsed.every((row) => Array.isArray(row) && row.length === WINDOW_SHAPE[1])
      ) {
        setJsonError(
          `Shape error: expected ${WINDOW_SHAPE[0]} rows × ${WINDOW_SHAPE[1]} columns ` +
          `(${FEATURE_NAMES.join(', ')}).`
        );
        setWindowData(null);
      } else {
        setJsonError('');
        setWindowData(parsed);
      }
    } catch {
      setJsonError('Invalid JSON.');
      setWindowData(null);
    }
  };

  const handleWindowUpdate = async () => {
    if (!windowData) {
      setMessage('Fix JSON errors before saving.');
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      const response = await fetch(`${API_BASE}/api/admin/update`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(windowData),
      });
      const data = await response.json();
      setMessage(data.error ? 'Error: ' + data.error : data.message);
    } catch (err) {
      setMessage('Network error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="admin-panel" aria-label="Admin panel">
      <h2>Admin Panel</h2>
      <p className="admin-hint">
        The prediction window is a {WINDOW_SHAPE[0]}×{WINDOW_SHAPE[1]} array of
        recent weather readings ({FEATURE_NAMES.join(', ')}). Editing it
        shifts what the model uses as its starting context.
      </p>

      <div className="admin-actions">
        <button onClick={fetchWindowData} disabled={loading}>
          {loading ? 'Loading…' : 'Load Window'}
        </button>
        <button onClick={handleWindowUpdate} disabled={loading || !windowData}>
          {loading ? 'Saving…' : 'Save Window'}
        </button>
      </div>

      {message && (
        <p
          className={message.startsWith('Error') ? 'error' : 'success-msg'}
          role="status"
        >
          {message}
        </p>
      )}

      {rawText && (
        <div className="window-data">
          <label htmlFor="window-textarea">
            <strong>Window data (editable JSON):</strong>
          </label>
          <textarea
            id="window-textarea"
            rows="14"
            value={rawText}
            onChange={handleTextChange}
            aria-label="Window data JSON"
            spellCheck={false}
          />
          {jsonError && (
            <p className="error" role="alert">
              {jsonError}
            </p>
          )}
        </div>
      )}
    </section>
  );
};

export default AdminPanel;
