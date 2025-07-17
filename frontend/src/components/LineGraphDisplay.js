import React from 'react';

const LineGraphDisplay = ({ data }) => {
  if (!data) {
    return (
      <section className="feature-predictions">
        <h2>Feature Predictions</h2>
        <p>Loading prediction charts...</p>
      </section>
    );
  }

  // Generate sample historical data for line graphs
  const generateHistoricalData = (feature, currentValue) => {
    const hours = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'];
    const baseValue = currentValue;
    return hours.map((hour, index) => {
      // Add some realistic variation to the data
      const variation = (Math.random() - 0.5) * (baseValue * 0.3);
      return Math.max(0, baseValue + variation);
    });
  };

  const temperatureData = generateHistoricalData(data.temp_c, data.temp_c);
  const humidityData = generateHistoricalData(data.humidity, data.humidity);
  const windData = generateHistoricalData(data.wind_speed, data.wind_speed);
  const rainData = generateHistoricalData(data.rain_probability, data.rain_probability);

  const maxTemp = Math.max(...temperatureData);
  const maxHumidity = Math.max(...humidityData);
  const maxWind = Math.max(...windData);
  const maxRain = Math.max(...rainData);

  return (
    <section className="feature-predictions">
      <h2>Feature Predictions</h2>
      <div className="charts-grid">
        <div className="chart-container">
          <h3>🌡️ Temperature (°C)</h3>
          <div className="line-chart">
            <svg width="200" height="100" viewBox="0 0 200 100">
              <polyline
                fill="none"
                stroke="#ff6b6b"
                strokeWidth="2"
                points={temperatureData.map((value, index) => {
                  const x = (index / (temperatureData.length - 1)) * 200;
                  const y = 100 - (value / maxTemp) * 100;
                  return `${x},${y}`;
                }).join(' ')}
              />
              <circle
                cx={200}
                cy={100 - (data.temp_c / maxTemp) * 100}
                r="3"
                fill="#ff6b6b"
              />
            </svg>
          </div>
          <div className="chart-x-axis">
            <span>00:00</span>
            <span>04:00</span>
            <span>08:00</span>
            <span>12:00</span>
            <span>16:00</span>
            <span>20:00</span>
          </div>
          <p>Current: {data.temp_c}°C</p>
        </div>

        <div className="chart-container">
          <h3>💧 Humidity (%)</h3>
          <div className="line-chart">
            <svg width="200" height="100" viewBox="0 0 200 100">
              <polyline
                fill="none"
                stroke="#4ecdc4"
                strokeWidth="2"
                points={humidityData.map((value, index) => {
                  const x = (index / (humidityData.length - 1)) * 200;
                  const y = 100 - (value / maxHumidity) * 100;
                  return `${x},${y}`;
                }).join(' ')}
              />
              <circle
                cx={200}
                cy={100 - (data.humidity / maxHumidity) * 100}
                r="3"
                fill="#4ecdc4"
              />
            </svg>
          </div>
          <div className="chart-x-axis">
            <span>00:00</span>
            <span>04:00</span>
            <span>08:00</span>
            <span>12:00</span>
            <span>16:00</span>
            <span>20:00</span>
          </div>
          <p>Current: {data.humidity}%</p>
        </div>

        <div className="chart-container">
          <h3>💨 Wind Speed (m/s)</h3>
          <div className="line-chart">
            <svg width="200" height="100" viewBox="0 0 200 100">
              <polyline
                fill="none"
                stroke="#45b7d1"
                strokeWidth="2"
                points={windData.map((value, index) => {
                  const x = (index / (windData.length - 1)) * 200;
                  const y = 100 - (value / maxWind) * 100;
                  return `${x},${y}`;
                }).join(' ')}
              />
              <circle
                cx={200}
                cy={100 - (data.wind_speed / maxWind) * 100}
                r="3"
                fill="#45b7d1"
              />
            </svg>
          </div>
          <div className="chart-x-axis">
            <span>00:00</span>
            <span>04:00</span>
            <span>08:00</span>
            <span>12:00</span>
            <span>16:00</span>
            <span>20:00</span>
          </div>
          <p>Current: {data.wind_speed} m/s</p>
        </div>

        <div className="chart-container">
          <h3>🌧️ Rain Probability (%)</h3>
          <div className="line-chart">
            <svg width="200" height="100" viewBox="0 0 200 100">
              <polyline
                fill="none"
                stroke="#96ceb4"
                strokeWidth="2"
                points={rainData.map((value, index) => {
                  const x = (index / (rainData.length - 1)) * 200;
                  const y = 100 - (value / maxRain) * 100;
                  return `${x},${y}`;
                }).join(' ')}
              />
              <circle
                cx={200}
                cy={100 - (data.rain_probability / maxRain) * 100}
                r="3"
                fill="#96ceb4"
              />
            </svg>
          </div>
          <div className="chart-x-axis">
            <span>00:00</span>
            <span>04:00</span>
            <span>08:00</span>
            <span>12:00</span>
            <span>16:00</span>
            <span>20:00</span>
          </div>
          <p>Current: {data.rain_probability}%</p>
        </div>
      </div>
    </section>
  );
};

export default LineGraphDisplay;
