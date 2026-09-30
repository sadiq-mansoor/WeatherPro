import React from 'react';

/**
 * Renders a 7-day forecast grid.
 * Each card shows day label, temperature, humidity, wind speed, and rain probability.
 */
function Forecast({ data }) {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <section className="forecast">
        <h2>7-Day Forecast</h2>
        <p className="loading-text">Loading forecast…</p>
      </section>
    );
  }

  return (
    <section className="forecast">
      <h2>7-Day Forecast</h2>
      <div className="forecast-cards">
        {data.map((day, index) => (
          <div className="forecast-card" key={index}>
            <h3>{day.day}</h3>
            <p>🌡 Temperature: {day.temperature} °C</p>
            <p>💧 Humidity: {day.humidity} %</p>
            <p>💨 Wind Speed: {day.wind_speed} m/s</p>
            <p>🌧 Rain Probability: {Math.round(day.rain_probability)}%</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default Forecast;
