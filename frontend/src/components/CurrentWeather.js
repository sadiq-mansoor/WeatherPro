import React from 'react';

const CurrentWeather = ({ data }) => {
  if (!data) {
    return (
      <section className="current-weather">
        <h2>Current Weather</h2>
        <p>Loading current weather...</p>
      </section>
    );
  }

  return (
    <section className="current-weather">
      <h2>Current Weather</h2>
      <div className="weather-card">
        <div className="weather-feature">
          <div className="feature-icon temperature-icon">🌡️</div>
          <div className="feature-details">
            <p className="feature-label">Temperature</p>
            <p className="feature-value">{data.temp_c}°C ({data.temp_f}°F)</p>
          </div>
        </div>

        <div className="weather-feature">
          <div className="feature-icon humidity-icon">💧</div>
          <div className="feature-details">
            <p className="feature-label">Humidity</p>
            <p className="feature-value">{data.humidity}%</p>
          </div>
        </div>

        <div className="weather-feature">
          <div className="feature-icon wind-icon">💨</div>
          <div className="feature-details">
            <p className="feature-label">Wind Speed</p>
            <p className="feature-value">{data.wind_speed} m/s</p>
          </div>
        </div>

        <div className="weather-feature">
          <div className="feature-icon rain-icon">🌧️</div>
          <div className="feature-details">
            <p className="feature-label">Rain Probability</p>
            <p className="feature-value">{data.rain_probability}%</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CurrentWeather;