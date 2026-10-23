import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import CurrentWeather from './components/CurrentWeather';
import Forecast from './components/Forecast';
import SimpleFeatureDisplay from './components/SimpleFeatureDisplay';
import AdminPanel from './components/AdminPanel';
import API_BASE from './config';

const REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

function App() {
  const [currentWeather, setCurrentWeather] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [weatherError, setWeatherError] = useState(null);
  const [forecastError, setForecastError] = useState(null);

  const [isAdmin, setIsAdmin] = useState(false);
  const [adminToken, setAdminToken] = useState('');
  const [loginError, setLoginError] = useState('');

  // ── Data fetching ────────────────────────────────────────────────────────────

  const fetchCurrentWeather = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/current`);
      const data = await response.json();
      if (data.error) {
        setWeatherError(data.error);
        setCurrentWeather(null);
      } else {
        setCurrentWeather(data);
        setWeatherError(null);
      }
    } catch (err) {
      setWeatherError('Could not reach the weather server.');
    }
  }, []);

  const fetchForecast = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/forecast`);
      const data = await response.json();
      if (data.forecast && Array.isArray(data.forecast)) {
        const mapped = data.forecast.map((item) => ({
          day: new Date(item.timestamp).toLocaleDateString(undefined, {
            weekday: 'long',
          }),
          temperature: item.temp_c.toFixed(1),
          humidity: item.humidity.toFixed(1),
          wind_speed: item.wind_speed.toFixed(1),
          rain_probability: item.rain_probability,
        }));
        setForecast(mapped);
        setForecastError(null);
      } else {
        setForecast([]);
        setForecastError(data.error || 'Unexpected forecast response.');
      }
    } catch (err) {
      setForecastError('Could not reach the weather server.');
    }
  }, []);

  useEffect(() => {
    fetchCurrentWeather();
    fetchForecast();
    const interval = setInterval(() => {
      fetchCurrentWeather();
      fetchForecast();
    }, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchCurrentWeather, fetchForecast]);

  // ── Admin auth ───────────────────────────────────────────────────────────────

  const handleAdminLogin = async () => {
    if (!adminToken.trim()) {
      setLoginError('Please enter an admin token.');
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/api/admin/verify`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${adminToken}` },
      });
      if (response.ok) {
        setIsAdmin(true);
        setLoginError('');
      } else {
        setLoginError('Invalid admin token.');
      }
    } catch (err) {
      setLoginError('Could not reach server: ' + err.message);
    }
  };

  const handleAdminLogout = () => {
    setIsAdmin(false);
    setAdminToken('');   // clear token from state on logout
    setLoginError('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleAdminLogin();
  };

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-title">
          <h1>🌦 Weather Forecast — Peshawar</h1>
          <p className="header-subtitle">
            Powered by LSTM · NCAI, UET Peshawar
          </p>
        </div>

        {!isAdmin ? (
          <div className="admin-login" role="form" aria-label="Admin login">
            <input
              type="password"
              placeholder="Admin token"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
              onKeyDown={handleKeyDown}
              aria-label="Admin token"
            />
            <button onClick={handleAdminLogin}>Login</button>
            {loginError && (
              <p className="error" role="alert">
                {loginError}
              </p>
            )}
          </div>
        ) : (
          <button className="logout-btn" onClick={handleAdminLogout}>
            Logout
          </button>
        )}
      </header>

      <main>
        {weatherError && (
          <p className="api-error" role="alert">
            ⚠ Current weather unavailable: {weatherError}
          </p>
        )}
        <CurrentWeather data={currentWeather} />

        {forecastError && (
          <p className="api-error" role="alert">
            ⚠ Forecast unavailable: {forecastError}
          </p>
        )}
        <Forecast data={forecast} />

        <SimpleFeatureDisplay data={currentWeather} />

        {isAdmin && <AdminPanel adminToken={adminToken} />}
      </main>
    </div>
  );
}

export default App;
