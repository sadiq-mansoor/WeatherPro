import React, { useState, useEffect } from 'react';
import './App.css';
import CurrentWeather from './components/CurrentWeather';
import Forecast from './components/Forecast';
import SimpleFeatureDisplay from './components/SimpleFeatureDisplay';
import AdminPanel from './components/AdminPanel';
import API_BASE from './config';

function App() {
  const [currentWeather, setCurrentWeather] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminToken, setAdminToken] = useState('');
  const [loginError, setLoginError] = useState('');

  useEffect(() => {
    fetchCurrentWeather();
    fetchForecast();

    // Refresh data every 5 minutes
    const interval = setInterval(() => {
      fetchCurrentWeather();
      fetchForecast();
    }, 300000);

    return () => clearInterval(interval);
  }, []);

  const fetchCurrentWeather = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/current`);
      const data = await response.json();
      setCurrentWeather(data);
    } catch (error) {
      console.error('Error fetching current weather:', error);
    }
  };

  const fetchForecast = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/forecast`);
      const data = await response.json();
      if (data.forecast && Array.isArray(data.forecast)) {
        const mappedForecast = data.forecast.map(item => ({
          day: new Date(item.timestamp).toLocaleDateString(undefined, { weekday: 'long' }),
          temperature: item.temp_c.toFixed(1),
          humidity: item.humidity.toFixed(1),
          wind_speed: item.wind_speed.toFixed(1),
          rain_probability: item.rain_probability
        }));
        setForecast(mappedForecast);
      } else {
        setForecast([]);
      }
    } catch (error) {
      console.error('Error fetching forecast:', error);
    }
  };

  const handleAdminLogin = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/verify`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${adminToken}` }
      });
      if (response.ok) {
        setIsAdmin(true);
        setLoginError('');
      } else {
        setLoginError('Invalid admin token');
      }
    } catch (error) {
      setLoginError('Could not reach server: ' + error.message);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🌦 Weather Forecast for Peshawar</h1>

        {!isAdmin ? (
          <div className="admin-login">
            <h2>Admin Login</h2>
            <input
              type="password"
              placeholder="Admin Token"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
            />
            <button onClick={handleAdminLogin}>Login</button>
            {loginError && <p className="error">{loginError}</p>}
          </div>
        ) : (
          <button onClick={() => setIsAdmin(false)}>Logout</button>
        )}
      </header>

      <main>
        <CurrentWeather data={currentWeather} />
        <Forecast data={forecast} />
        <SimpleFeatureDisplay data={currentWeather} />

        {isAdmin && <AdminPanel adminToken={adminToken} />}
      </main>
    </div>
  );
}

export default App;
