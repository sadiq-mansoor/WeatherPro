import React from 'react';

const SimpleFeatureDisplay = ({ data }) => {
  if (!data) {
    return (
      <section className="feature-predictions">
        <h2>Feature Predictions</h2>
        <p>Loading prediction charts...</p>
      </section>
    );
  }

  return (
    <section className="feature-predictions">
      <h2>Feature Predictions</h2>
      <div className="charts-grid">
        <div className="chart-container">
          <h3>🌡️ Temperature</h3>
          <div className="simple-chart">
            <div className="chart-bar-container">
              <div className="chart-bar" style={{ height: '60%', backgroundColor: '#ff6b6b' }}></div>
              <div className="chart-label">{data.temp_c}°C</div>
            </div>
          </div>
          <p>Current: {data.temp_c}°C</p>
        </div>

        <div className="chart-container">
          <h3>💧 Humidity</h3>
          <div className="simple-chart">
            <div className="chart-bar-container">
              <div className="chart-bar" style={{ height: '70%', backgroundColor: '#4ecdc4' }}></div>
              <div className="chart-label">{data.humidity}%</div>
            </div>
          </div>
          <p>Current: {data.humidity}%</p>
        </div>

        <div className="chart-container">
          <h3>💨 Wind Speed</h3>
          <div className="simple-chart">
            <div className="chart-bar-container">
              <div className="chart-bar" style={{ height: '40%', backgroundColor: '#45b7d1' }}></div>
              <div className="chart-label">{data.wind_speed} m/s</div>
            </div>
          </div>
          <p>Current: {data.wind_speed} m/s</p>
        </div>

        <div className="chart-container">
          <h3>🌧️ Rain Probability</h3>
          <div className="simple-chart">
            <div className="chart-bar-container">
              <div className="chart-bar" style={{ height: '30%', backgroundColor: '#96ceb4' }}></div>
              <div className="chart-label">{data.rain_probability}%</div>
            </div>
          </div>
          <p>Current: {data.rain_probability}%</p>
        </div>
      </div>
    </section>
  );
};

export default SimpleFeatureDisplay;
