import React from 'react';

function Forecast({ data }) {
  // Ensure data is an array before mapping
  if (!Array.isArray(data)) {
    return <p>Loading forecast data...</p>;
  }

  return (
    <div className="forecast">
      <h2>5-Day Forecast</h2>
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
    </div>
  );
}

export default Forecast;
