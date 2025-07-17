import React from 'react';

const FeaturePredictionsChart = ({ data }) => {
  if (!data) {
    return (
      <section className="feature-predictions">
        <h2>Feature Predictions</h2>
        <p>Loading prediction charts...</p>
      </section>
    );
  }

  // Generate sample historical data for demonstration (in real app, this would come from backend)
  const generateHistoricalData = (feature, currentValue) => {
    const hours = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'];
    const baseValue = currentValue;
    return hours.map((hour, index) => {
      // Add some realistic variation to the data
      const variation = (Math.random() - 0.5) * (baseValue * 0.2);
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

  const createBarChart = (data, maxValue, color) => {
    return data.map((value, index) => {
      const height = (value / maxValue) * 100;
      return (
        <div key={index} className="chart-bar-container">
          <div
            className="chart-bar"
            style={{
              height: `${height}%`,
              backgroundColor: color,
            }}
          ></div>
          <div className="chart-label">{Math.round(value)}</div>
        </div>
      );
    });
  };

  return (
    <section className="feature-predictions">
      <h2>Feature Predictions</h2>
      <div className="charts-grid">
        <div className="chart-container">
          <h3>🌡️ Temperature (°C)</h3>
          <div className="simple-chart">
            {createBarChart(temperatureData, maxTemp, '#ff6b6b')}
          </div>
          <div className="chart-x-axis">
            <span>00:00</span>
            <span>04:00</span>
            <span>08:00</span>
            <span>12:00</span>
            <span>16:00</span>
            <span>20:00</span>
          </div>
        </div>

        <div className="chart-container">
          <h3>💧 Humidity (%)</h3>
          <div className="simple-chart">
            {createBarChart(humidityData, maxHumidity, '#4ecdc4')}
          </div>
          <div className="chart-x-axis">
            <span>00:00</span>
            <span>04:00</span>
            <span>08:00</span>
            <span>12:00</span>
            <span>16:00</span>
            <span>20:00</span>
          </div>
        </div>

        <div className="chart-container">
          <h3>💨 Wind Speed (m/s)</h3>
          <div className="simple-chart">
            {createBarChart(windData, maxWind, '#45b7d1')}
          </div>
          <div className="chart-x-axis">
            <span>00:00</span>
            <span>04:00</span>
            <span>08:00</span>
            <span>12:00</span>
            <span>16:00</span>
            <span>20:00</span>
          </div>
        </div>

        <div className="chart-container">
          <h3>🌧️ Rain Probability (%)</h3>
          <div className="simple-chart">
            {createBarChart(rainData, maxRain, '#96ceb4')}
          </div>
          <div className="chart-x-axis">
            <span>00:00</span>
            <span>04:00</span>
            <span>08:00</span>
            <span>12:00</span>
            <span>16:00</span>
            <span>20:00</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default FeaturePredictionsChart;
