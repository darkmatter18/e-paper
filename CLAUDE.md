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
┌──────────────────┬──────────────────┐
│  ClockWidget     │  WeatherWidget   │
│  (0,0,400x240)   │  (400,0,400x240) │
│  Analog + Digital│  Current + 5-day │
├──────────────────┼──────────────────┤
│  DateWidget      │  QuoteWidget     │
│  (0,240,400x240) │  (400,240,400x240│
│  Day + Date      │  Quote + Author  │
└──────────────────┴──────────────────┘
```

**Entry Point:**
- `main.py` → imports and calls `clock()` from `display_clock.py`
- `display_clock.py` orchestrates widgets and manages display refresh cycles

**Widget Architecture:**

Modular widget system with abstract base class:

```
widgets/
├── widget.py                # Abstract Widget + WidgetRegion
├── clock_widget.py          # Analog + digital clock (supports partial refresh)
├── date_widget.py           # Day of week + date
├── weather_widget.py        # Current weather + 5-day forecast
└── quote_widget.py          # Quote of the day with dynamic sizing
```

**Widget Interface:**
```python
class Widget(ABC):
    def __init__(self, region: WidgetRegion)
    
    @abstractmethod
    def draw(self, black_draw, red_draw=None, **kwargs)
    
    def draw_decorations(self, black_draw)
    def draw_red_decorations(self, red_draw)
    
    @property
    def supports_partial_refresh(self) -> bool
```

**Key Concepts:**
- Each widget owns its screen region (`WidgetRegion` with x, y, width, height)
- Widgets draw at their absolute coordinates in full display space
- Widgets can support partial refresh by setting `supports_partial_refresh = True`
- Weather and Quote widgets own their data sources (no external service passing needed)

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

**Service Ownership:**
- Quote service: owned by QuoteWidget
- Weather service: owned by WeatherWidget
- Services cache internally (quote by date, weather by time)

**Fonts:**
- Located in `fonts/` directory
- Loaded at module level as constants in each widget
- Fonts used: Geomini, HennyPenny, PlayfairDisplay, Righteous, WeatherIcons

## Key Components in display_clock.py

**PartialStateManager:**
- Manages previous state for partial-refresh widgets
- `get_old_region(widget)`: Retrieve previous region image
- `update_state(widget, new_region)`: Store new region image
- `update_from_full_frame(full_frame)`: Extract and store all widget regions after full refresh
- `has_state()`: Check if any state is stored

**Core Functions:**
- `full_refresh(epd, now, state_manager)`: Full display refresh with all widgets and red channel
- `partial_refresh(epd, now, state_manager)`: Refresh each partial-refresh widget independently
- `extract_region(image, x, y, width, height)`: Crop region from full display image
- `to_buffer(image)`: Convert PIL image to e-paper buffer (handles polarity correctly)

**Refresh Flow:**
1. Full refresh (every 15 min):
   - Render all widgets to full 800x480 display
   - Send to e-paper with red channel
   - Extract regions for partial-refresh widgets
   - Store in PartialStateManager

2. Partial refresh (every minute):
   - For each widget with `supports_partial_refresh=True`:
     - Get old region from state manager
     - Render widget to temp full image
     - Extract widget's region
     - Send old + new region buffers to e-paper (region-specific)
     - Update state manager with new region

**Constants:**
- `DISPLAY_W, DISPLAY_H = 800, 480`
- `ALL_WIDGETS = [clock_widget, date_widget, weather_widget, quote_widget]`
- `FULL_REFRESH_MIN = 15` (full refresh interval in minutes)

## Adding New Features

**Adding a new widget:**
1. Create `widgets/<name>_widget.py`
2. Inherit from `Widget` and define `WidgetRegion` in `__init__()`
3. Implement `draw(black_draw, red_draw=None, **kwargs)` method
4. Optionally implement `draw_decorations()` and `draw_red_decorations()`
5. Set `supports_partial_refresh = True` if widget should update every minute (black-only)
6. Export in `widgets/__init__.py`
7. Add to `ALL_WIDGETS` list in `display_clock.py`

**Widget Guidelines:**
- Draw at your widget's absolute coordinates (`self.region.x`, `self.region.y`)
- If widget owns a service, instantiate it in `__init__()` and fetch data in `draw()`
- Partial refresh widgets MUST work without red channel (`red_draw=None`)
- Use dynamic sizing/wrapping for text to prevent overflow

**Adding a new service:**
1. Create `services/<name>/` directory
2. Define abstract base class + data models in `<name>_service.py`
3. Implement concrete service (e.g., `openweathermap_service.py`)
4. Create `__init__.py` to export public classes
5. Add caching inside service implementation (by date/time as appropriate)
6. Widget that needs the service owns and instantiates it

**Color Usage:**
- Black channel (`black` image): Main content, always visible
- Red channel (`red` image): Accents, hour hand, some decorative elements
- Red only updates on full refresh (every 15 min / hour change)
- Partial refresh is BLACK-ONLY (red elements cannot be partially refreshed)

## Deployment Notes

- Target platform: Raspberry Pi (ARM)
- Runs as systemd service with auto-restart on failure
- Service user: `arkadip` (configured in `epaper-clock.service`)
- Working directory: `/home/arkadip/e-paper`
- Virtual environment: `/home/arkadip/e-paper/.venv`

## Code Documentation

All modules, classes, methods, and functions are documented with comprehensive Google-style docstrings:

**Core Display Module:**
- `display_clock.py`: Main orchestration, PartialStateManager, refresh cycles
  - Module-level docs: Architecture overview, hardware details
  - Class docs: PartialStateManager with state tracking details
  - Function docs: full_refresh(), partial_refresh(), clock() with complete workflows
  - Side Effects sections for hardware interaction functions

**Widget Modules:**
- `widgets/widget.py`: Base Widget class and WidgetRegion dataclass
  - Abstract interface with partial refresh contracts
  - Hardware constraints (e-paper dual-channel, polarity)
- `widgets/clock_widget.py`: Analog + digital clock with partial refresh
  - Smooth hour hand algorithm, coordinate system details
  - Constants documented (CX, CY, RADIUS, HOUR_LEN, MIN_LEN, fonts)
- `widgets/date_widget.py`: Day + date with scalloped borders
  - Typography strategy, decorative elements
  - Font constants and region layout
- `widgets/weather_widget.py`: Current weather + 5-day forecast
  - OpenWeatherMap integration, Weather Icons font mapping
  - API configuration via environment variables
- `widgets/quote_widget.py`: Quote with adaptive font sizing
  - Dynamic sizing algorithm, Playfair Display typography
  - Text wrapping strategy

**Utility Modules:**
- `utils/datetime_util.py`: Timezone-aware datetime (IST)
  - Static methods for timezone conversion
  - IST constant (UTC+5:30)

**Service Modules:**
- `services/quote/`: Abstract service + ZenQuotes implementation
  - Quote dataclass with text and author fields
  - Abstract QuoteService interface
  - ZenQuotesService with date-based caching
  - API integration details, fallback mechanism
- `services/weather/`: Abstract service + OpenWeatherMap implementation
  - CurrentWeather, ForecastDay, WeatherData dataclasses
  - Abstract WeatherService interface
  - OpenWeatherMapService with API integration
  - Forecast aggregation from 3-hour intervals to daily summaries
  - Caching recommendations (10-30 minutes)

**Documentation Standards:**
- Google-style docstrings throughout
- Type hints on all functions/methods/parameters
- Args, Returns, Raises, Note sections where applicable
- Side Effects documented for hardware interaction
- Hardware constraints documented inline (e-paper polarity, partial refresh limitations)
- Caching strategies explained in service implementations
- API integration details (endpoints, authentication, rate limits)
- **No usage examples or code snippets** - focused on API contracts only

## Testing

No automated tests currently. To verify changes:
1. Run locally: `uv run python -m main`
2. Watch for display updates every minute
3. Full refresh occurs at :00, :15, :30, :45 past the hour
4. Check logs for API call patterns (quote should fetch once per day)
5. Verify partial refresh updates clock without ghosting
