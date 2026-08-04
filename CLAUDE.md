# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

E-paper display clock for Waveshare 7.5" B/V2 (800x480, black/white/red) running on Raspberry Pi. Displays analog + digital clock, date, and quote of the day with decorative elements.

## Setup & Commands

```bash
# Install dependencies
uv sync

# Run locally (for development/testing)
uv run python -m main

# Deploy as systemd service (production on Raspberry Pi)
sudo cp epaper-clock.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable epaper-clock
sudo systemctl start epaper-clock

# Monitor service
sudo systemctl status epaper-clock
journalctl -u epaper-clock -f
```

## Environment Configuration

Create `.env` file from `.env.example`:
- `OPENWEATHER_API_KEY`: OpenWeatherMap API key (optional, for future weather widget)
- `LATITUDE` / `LONGITUDE`: Location coordinates (optional, for weather)

## Hardware Constraints (CRITICAL)

**Waveshare 7.5" B/V2 E-Paper Display:**
- Resolution: 800x480
- Colors: Black, White, Red
- **Partial refresh is BLACK-ONLY**: Red pigment requires full (flashing) refresh to activate or erase
- Driver: `lib/waveshare_epd/epd7in5b_V2.py` (read-only, from Waveshare)

**Refresh Strategy:**
- Full refresh: Every 15 minutes + on hour change (to redraw red elements)
- Partial refresh: Between full refreshes (black-only, for minute hand updates)
- Display sleeps between updates to save power

**Buffer Polarity:**
- `display()` inverts black buffer before sending (line 209-211 of driver)
- `display_Partial()` sends buffer as-is with NO inversion
- `to_buffer()` helper returns raw PIL bytes (1=white, 0=black) for partial refresh

**Partial Refresh After Sleep:**
- After `epd.sleep()` → `epd.init_part()`, controller RAM is cleared
- Must send previous frame as "old" buffer (command 0x10) so controller knows what to erase
- Use `partial_refresh_with_old()` instead of driver's `display_Partial()` to track previous frame

## Architecture

**Display Layout (800x480):**
```
┌─────────────────┬─────────────────┐
│ Upper-Left      │ Right Panel     │
│ (400x240)       │ (400x480)       │
│ Analog + Digital│ Quote of Day    │
│ Clock           │                 │
├─────────────────┤                 │
│ Bottom-Left     │                 │
│ (400x240)       │                 │
│ Date            │                 │
└─────────────────┴─────────────────┘
```

**Entry Point:**
- `main.py` → imports and calls `clock()` from `display_clock.py`
- `display_clock.py` contains all rendering logic and main loop

**Service Architecture:**

Services are organized into submodules with abstract base classes:

```
services/
├── quote/
│   ├── quote_service.py      # Abstract QuoteService + Quote dataclass
│   └── zenquotes_service.py  # ZenQuotesService (with daily caching)
└── weather/
    ├── weather_service.py           # Abstract WeatherService + data models
    └── openweathermap_service.py    # OpenWeatherMapService
```

**Import pattern:**
```python
from services.quote import Quote, QuoteService, ZenQuotesService
from services.weather import WeatherData, WeatherService, OpenWeatherMapService
```

**Service Caching:**
- Quote service caches by date internally - just call `get_quote_of_the_day()` on every full refresh
- Weather service (when integrated) should follow same pattern

**Fonts:**
- Located in `fonts/` directory
- Loaded at module level as constants (FONT_DIGI, FONT_DATE_DAY, etc.)
- Two fonts used: Geomini-VariableFont_wght.ttf and HennyPenny-Regular.ttf

## Key Functions in display_clock.py

**Rendering:**
- `full_refresh(epd, now, quote_service)`: Full display refresh with red channel
- `partial_refresh_with_old(...)`: Custom partial refresh that tracks previous frame
- `render_region(...)`: Renders clock region for partial refresh
- `to_buffer(image)`: Converts PIL image to e-paper buffer (handles polarity correctly)

**Drawing Functions:**
- `draw_static()`, `draw_hour_hand()`, `draw_minute_hand()`: Clock components
- `draw_digital()`: HH/MM/AM-PM stack (hour in red)
- `draw_date()`: Weekday + full date
- `draw_quote()`: Quote text + author with wrapping
- `draw_*_decorations()`: Black decorations (dots, brackets, borders)
- `draw_*_red_decorations()`: Red accent elements

**Layout Constants:**
- `DISPLAY_W, DISPLAY_H = 800, 480`
- `CX, CY = 100, 120` (analog clock center)
- `DIGI_X = 240` (digital clock left edge)
- `FULL_REFRESH_MIN = 15` (full refresh interval in minutes)

## Adding New Features

**Adding a new service (e.g., weather):**
1. Create `services/<name>/` directory
2. Define abstract base class + data models in `<name>_service.py`
3. Implement concrete service (e.g., `openweathermap_service.py`)
4. Create `__init__.py` to export public classes
5. Add caching inside service implementation (by date/time as appropriate)
6. Import in `display_clock.py` and integrate into `full_refresh()`

**Adding widgets to right panel:**
- Right panel (400x480) currently shows quote only
- Add drawing functions: `draw_<widget>()` and `draw_<widget>_decorations()`
- Call from `full_refresh()` after fetching data
- Remember: red elements only in full refresh, not partial

**Color Usage:**
- Black channel (`black` image): Main content, always visible
- Red channel (`red` image): Accents, hour hand, some decorative elements
- Red only updates on full refresh (every 15 min / hour change)

## Deployment Notes

- Target platform: Raspberry Pi (ARM)
- Runs as systemd service with auto-restart on failure
- Service user: `arkadip` (configured in `epaper-clock.service`)
- Working directory: `/home/arkadip/e-paper`
- Virtual environment: `/home/arkadip/e-paper/.venv`

## Testing

No automated tests currently. To verify changes:
1. Run locally: `uv run python -m main`
2. Watch for display updates every minute
3. Full refresh occurs at :00, :15, :30, :45 past the hour
4. Check logs for API call patterns (quote should fetch once per day)
