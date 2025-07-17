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
- OpenWeatherMap API Key (**required** — free tier works; get one at https://openweathermap.org/api)

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
- `POST /api/admin/verify` - Verify an admin token (used by the frontend login)
- `GET /api/admin/window` - Get current prediction window data
- `POST /api/admin/update` - Update prediction window data

## Admin Panel

To access the admin panel:
1. Set the `ADMIN_TOKEN` env var on the backend to a secret value. If it is left unset, all admin endpoints are disabled.
2. On the main page, enter that token and click "Login". The token is sent to the backend (`POST /api/admin/verify`) and verified server-side with a constant-time comparison — the browser never holds any secret.
3. Once verified, access advanced features like viewing/modifying the prediction window and history.

## Configuration

Copy `backend/.env.example` to `backend/.env` and fill in your values (the `.env` file is git-ignored).

### Environment Variables
- `OPENWEATHER_API_KEY` (**required**): Your OpenWeatherMap API key — get one at https://openweathermap.org/api
- `ADMIN_TOKEN` (optional): Secret token for the admin panel. If unset, admin endpoints are disabled entirely. Set it to a strong value to enable admin access.

### Files
- `best_lstm.keras`: Trained LSTM model
- `scaler_X.pkl`, `scaler_y.pkl`: Feature scalers
- `window.npy`: Current prediction window (30x5 features)
- `history.npy`: Prediction history
- `predictions.log`: Application logs

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

## Deployment

### Frontend → Vercel
The React frontend deploys to Vercel as a static site (`vercel.json` at the repo root handles the build).

1. In Vercel, **Import** this GitHub repo and select the **`vercel-deploy`** branch.
2. Vercel reads `vercel.json` automatically (build: `frontend`, output: `frontend/build`).
3. Add an environment variable **`REACT_APP_API_URL`** = the URL of your deployed backend
   (see `frontend/.env.example`). Leave it unset only for local dev, where the CRA proxy is used.
4. Deploy.

### Backend → not Vercel
The Flask backend depends on **TensorFlow** and keeps persistent state, so it will **not** run on
Vercel's serverless functions (250 MB size limit + stateless execution). Host it on a container
platform instead — **Render**, **Railway**, **Fly.io**, or **Hugging Face Spaces** — then point
`REACT_APP_API_URL` at that deployment. The backend also needs its model files
(`best_lstm.keras`, `scaler_X.pkl`, `scaler_y.pkl`) present at runtime.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
