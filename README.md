# E Paper

## SYNC PROJECT

```bash
uv sync
```

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
