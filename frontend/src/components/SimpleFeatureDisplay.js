import React from 'react';

/**
 * Visual bar-chart summary of the four predicted weather features.
 * Bar heights are proportional to actual data values.
 */
const SimpleFeatureDisplay = ({ data }) => {
  if (!data) {
    return (
      <section className="feature-predictions">
        <h2>Prediction Summary</h2>
        <p className="loading-text">Loading predictions…</p>
      </section>
    );
  }

  // Define each metric with its domain max for bar scaling
  const metrics = [
    {
      label: 'Temperature',
      icon: '🌡️',
      value: data.temp_c,
      unit: '°C',
      max: 50,        // Peshawar summer max ~50 °C
      color: '#ff6b6b',
      className: 'temperature-icon',
    },
    {
      label: 'Humidity',
      icon: '💧',
      value: data.humidity,
      unit: '%',
      max: 100,
      color: '#4ecdc4',
      className: 'humidity-icon',
    },
    {
      label: 'Wind Speed',
      icon: '💨',
      value: data.wind_speed,
      unit: 'm/s',
      max: 30,        // generous upper bound for Peshawar winds
      color: '#45b7d1',
      className: 'wind-icon',
    },
    {
      label: 'Rain Probability',
      icon: '🌧️',
      value: data.rain_probability,
      unit: '%',
      max: 100,
      color: '#96ceb4',
      className: 'rain-icon',
    },
  ];

  return (
    <section className="feature-predictions">
      <h2>Prediction Summary</h2>
      <div className="charts-grid">
        {metrics.map(({ label, icon, value, unit, max, color, className }) => {
          const pct = Math.min(Math.max((value / max) * 100, 4), 100);
          return (
            <div className="chart-container" key={label}>
              <h3>
                <span className={`feature-icon ${className}`}>{icon}</span>{' '}
                {label}
              </h3>
              <div className="simple-chart" role="img" aria-label={`${label}: ${value}${unit}`}>
                <div className="chart-bar-container">
                  <div
                    className="chart-bar"
                    style={{ height: `${pct}%`, backgroundColor: color }}
                  />
                  <div className="chart-label">
                    {value}
                    {unit}
                  </div>
                </div>
              </div>
              <p className="chart-current">
                Current: <strong>{value}{unit}</strong>
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default SimpleFeatureDisplay;
