# E Paper

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Create `.env` file with your API keys and location:

```bash
cp .env.example .env
```

Edit `.env` and add:
- `OPENWEATHER_API_KEY`: Get from [OpenWeatherMap](https://openweathermap.org/api)
- `LATITUDE` and `LONGITUDE`: Your location coordinates

## Run project

```bash
uv run python -m main
```

## Run as background service

Copy the systemd unit file and enable it:

```bash
sudo cp epaper-clock.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable epaper-clock
sudo systemctl start epaper-clock
```

Check status / logs:

```bash
sudo systemctl status epaper-clock
journalctl -u epaper-clock -f
```

Stop the service:

```bash
sudo systemctl stop epaper-clock
```
