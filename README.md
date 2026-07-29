# Weather Forecast App

A full-stack weather prediction application that combines real-time weather data from OpenWeatherMap with machine learning predictions using an LSTM model to provide accurate forecasts for Peshawar.

## Data Sources

- **Primary sensor data** — collected from the **National Centre of Excellence (NCAI), UET Peshawar**, using the centre's own on-site weather sensors.
- **External / open data** — `OpenDatatemperature-and-rain-trends-peshawar-climate.csv` was obtained from an external open-data source (not NCAI sensors). Supplementary datasets also draw on external sources such as Visual Crossing and Kaggle.

## Features

- **Real-time Weather Data**: Fetches current weather conditions from OpenWeatherMap API
- **7-Day Forecast**: Provides weather predictions for the next 7 days using LSTM neural network
- **Interactive Frontend**: React-based UI with charts and visualizations
- **Admin Panel**: Secure admin interface for managing prediction windows and viewing history
- **Caching**: Optimized performance with weather data caching and model pre-compilation
- **Logging**: Comprehensive logging for predictions and API calls

## Tech Stack

### Backend
- **Flask**: Web framework for API endpoints
- **TensorFlow/Keras**: LSTM model for weather predictions
- **NumPy**: Numerical computations
- **Joblib**: Model and scaler serialization
- **Requests**: HTTP client for OpenWeatherMap API

### Frontend
- **React**: User interface framework
- **Chart.js**: Data visualization library
- **CSS**: Styling

## Prerequisites

- Python 3.8+
- Node.js 14+
- An OpenWeatherMap API key (**required** — get a free one at https://openweathermap.org/api)
- The trained model artifacts (see [Model artifacts](#model-artifacts-required) below)

## Installation

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # source venv/bin/activate  # On macOS/Linux
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env   # then edit .env
   ```
   Set `OPENWEATHER_API_KEY` and a strong `ADMIN_TOKEN` (see [Configuration](#configuration)).

5. Add the model artifacts (see [below](#model-artifacts-required)) — the server will not start without them.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

## Running the Application

### Start the Backend

1. Ensure you're in the backend directory and virtual environment is activated
2. Run the Flask server:
   ```bash
   python app.py
   ```

The backend will start on `http://localhost:5000`

### Start the Frontend

1. Open a new terminal and navigate to the frontend directory
2. Start the React development server:
   ```bash
   npm start
   ```

The frontend will start on `http://localhost:3000` and proxy API calls to the backend.

### Access the Application

- **Main Application**: http://localhost:3000
- **Backend API Home**: http://localhost:5000
- **Current Weather API**: http://localhost:5000/api/current
- **Forecast API**: http://localhost:5000/api/forecast

## API Endpoints

### Public Endpoints
- `GET /` - API status and available endpoints
- `GET /api/current` - Current weather prediction
- `GET /api/forecast` - 7-day weather forecast
- `GET /health` - Health check endpoint
- `GET /debug_predict` - Debug prediction data

### Admin Endpoints (Require Bearer Token)
- `GET /api/admin/window` - Get current prediction window data
- `POST /api/admin/update` - Update prediction window data
- `GET /api/admin/history` - Get prediction history

## Admin Panel

The admin token is **never checked in the browser** — the frontend sends it to the backend
(`/api/admin/verify`), which validates it against the `ADMIN_TOKEN` environment variable using a
constant-time comparison. If `ADMIN_TOKEN` is not set, the admin endpoints are disabled entirely.

To access the admin panel:
1. On the main page, enter the admin token you configured in `ADMIN_TOKEN`
2. Click "Login"
3. Access advanced features like viewing/modifying the prediction window and history

## Configuration

Copy `backend/.env.example` to `backend/.env` and fill in your values (the `.env` file is git-ignored).

### Environment Variables
- `OPENWEATHER_API_KEY` (**required**): Your OpenWeatherMap API key — get one at https://openweathermap.org/api
- `ADMIN_TOKEN` (**required for the admin panel**): Token for the admin endpoints. Use a long random string. If it is left unset, the admin endpoints are disabled and no admin login is possible.

### Files
- `best_lstm.keras`: Trained LSTM model
- `scaler_X.pkl`, `scaler_y.pkl`: Feature scalers
- `window.npy`: Current prediction window (30x5 features) — auto-created on first run
- `history.npy`: Prediction history — auto-created on first run
- `predictions.log`: Application logs

## Model artifacts (required)

The backend serves predictions from a pre-trained LSTM and its fitted scalers. These binary files
are **not committed to the repository** (they are large and environment-specific), so they must be
placed in the `backend/` directory before starting the server:

| File | Description |
|------|-------------|
| `best_lstm.keras` | Trained LSTM network |
| `scaler_X.pkl` | Fitted input feature scaler |
| `scaler_y.pkl` | Fitted target scaler |

The model expects an input window of shape **(30, 5)** — 30 timesteps of 5 features
(`pressure`, `dew_point_f`, `humidity`, `wind_speed`, `temp_f`) — and predicts temperature,
humidity, wind speed and rain probability.

If any of these files is missing, `python app.py` exits immediately with a message telling you
which artifact was not found. Contact the author for the trained weights, or retrain on comparable
NCAI/UET Peshawar sensor data to reproduce them.

## Troubleshooting

### Common Issues

1. **Model Loading Errors**: Ensure all model files (`best_lstm.keras`, scalers) are present in the backend directory
2. **API Key Issues**: Check your OpenWeatherMap API key if using a custom one
3. **Port Conflicts**: Ensure ports 3000 and 5000 are available
4. **CORS Errors**: The backend has CORS enabled for frontend communication

### Logs
Check `backend/predictions.log` for detailed error information.

## Development

### Backend Testing
```bash
# Test individual endpoints
curl http://localhost:5000/
curl http://localhost:5000/api/current
curl http://localhost:5000/api/forecast
```

### Frontend Testing
```bash
cd frontend
npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
