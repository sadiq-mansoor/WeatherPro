# Training data

The current approved working dataset is:

```text
data/raw/peshawar_weather_2000_2024.csv
```

It was downloaded from the [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
for latitude `34.008`, longitude `71.5785`, from 2000-01-01 through
2024-12-31. Open-Meteo provides reanalysis-based historical data, so this file
must be described as gridded historical weather data rather than direct station
observations. The source response contained 219,168 hourly rows. The pipeline
aggregated them to 9,132 daily rows using daily means for temperature, dew
point, humidity, wind speed, and pressure, and daily sums for precipitation.

The download and validation steps are reproducible with:

```powershell
python scripts/download_open_meteo.py
cd backend
$env:DATA_CSV = '..\\data\\raw\\peshawar_weather_2000_2024.csv'
python audit_dataset.py
```

The training pipeline expects these columns:

```text
date, city, tavg, dew_point, humidity, wspd, pressure, prcp
```

Values for `tavg` and `dew_point` are interpreted as Celsius and converted to
Fahrenheit by `backend/train_lstm.py`. `prcp` is interpreted as millimetres.
Only rows whose city contains `Peshawar` are used.

Do not compare a newly trained model with the legacy metrics until the same
dataset version and the current validation-only evaluation protocol have been
used. Keep the dataset checksum beside the resulting model artifacts.

To use another approved file without moving it:

```powershell
$env:DATA_CSV = 'D:\path\to\approved\dataset.csv'
cd backend
python train_lstm.py
```

Audit it before training:

```powershell
cd backend
python audit_dataset.py
```
