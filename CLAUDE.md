# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

E-paper display clock for Waveshare 7.5" B/V2 (800x480, black/white/red) running on Raspberry Pi. Features multiple screen layouts controlled via REST API, with widgets including analog clock, date, weather forecast, and quote of the day.

**Architecture:** FastAPI server with isolated display engine process, allowing dynamic screen switching without interrupting the rendering loop.

## Setup & Commands

```bash
# Install dependencies
uv sync

# Run API server (default mode - with screen switching)
uv run python main.py
# API runs on http://localhost:8000

# Run standalone (no API, single screen)
uv run python main_standalone.py

# Test API endpoints (without hardware)
python test_api.py

# Deploy as systemd service (production on Raspberry Pi)
sudo cp epaper-clock.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable epaper-clock
sudo systemctl start epaper-clock

# Monitor service
sudo systemctl status epaper-clock
journalctl -u epaper-clock -f

# API Usage Examples
# List available screens
curl http://localhost:8000/

# Check health
curl http://localhost:8000/health

# Switch screen
curl -X PUT http://localhost:8000/api/v1/screen \
     -H "Content-Type: application/json" \
     -d '{"screen": "todays_weather"}'
```

## API Quick Reference

**Base URL:** `http://localhost:8000` (configurable via `API_HOST`, `API_PORT`)

**Endpoints:**
- `GET /` - API info & available screens
- `GET /health` - Health check (engine status, current screen)
- `PUT /api/v1/screen` - Switch screen
  ```json
  {"screen": "datetime_weather_forecast"}  // or "todays_weather"
  ```

**Available Screens:**
- `datetime_weather_forecast` - 4-widget dashboard (clock, date, weather, quote)
- `todays_weather` - Full-screen weather with hourly forecast graph

**Example:**
```bash
curl -X PUT http://localhost:8000/api/v1/screen \
     -H "Content-Type: application/json" \
     -d '{"screen": "todays_weather"}'
```

## Environment Configuration

Create `.env` file from `.env.example`:
- `API_HOST`: API server bind address (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `OPENWEATHER_API_KEY`: OpenWeatherMap API key (required for weather widgets)
- `LATITUDE` / `LONGITUDE`: Location coordinates (required for weather)

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

**System Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│                      Main Process                        │
│  ┌────────────────────────────────────────────────────┐ │
│  │              FastAPI Server (main.py)               │ │
│  │  - REST API endpoints                               │ │
│  │  - Screen switching                                 │ │
│  │  - Health checks                                    │ │
│  │  Runs on: http://localhost:8000                     │ │
│  └─────────────────────┬──────────────────────────────┘ │
│                        │ Command Queue                   │
│                        │ (multiprocessing.Queue)         │
└────────────────────────┼─────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   Display Engine Process                 │
│  ┌────────────────────────────────────────────────────┐ │
│  │        Display Controller (display_controller.py)   │ │
│  │  - Main rendering loop                              │ │
│  │  - Full/partial refresh management                  │ │
│  │  - Hardware control (GPIO/SPI)                      │ │
│  │  - Command processing                               │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Available Screens:**

1. **datetime_weather_forecast** (default) - 4-widget dashboard:
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

2. **todays_weather** - Full-screen weather dashboard:
```
┌──────────────────────────────────────┐
│     TodaysWeatherWidget (800x480)    │
│  - Current weather (large temp, icon)│
│  - Stats bar (feels like, humidity)  │
│  - 24-hour temperature graph         │
│  - Hourly weather icons              │
└──────────────────────────────────────┘
```

**Entry Points:**
- `main.py` → Starts FastAPI server, spawns display engine process
- `main_standalone.py` → Direct display engine (no API, single screen)
- `display/display_main.py` → Display engine process entry point
- `display/display_controller.py` → Core rendering loop and hardware control

**Widget Architecture:**

Modular widget system with abstract base class:

```
widgets/
├── widget.py                     # Abstract Widget + WidgetRegion
├── clock_widget.py               # Analog + digital clock (supports partial refresh)
├── date_widget.py                # Day of week + date
├── weather_widget.py             # Current weather + 5-day forecast
├── quote_widget.py               # Quote of the day with dynamic sizing
└── todays_weather_widget.py      # Full-screen weather dashboard with hourly graph
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
- Weather service: owned by WeatherWidget, TodaysWeatherWidget
- Services cache internally (quote by date, weather by time)

**Fonts:**
- Centralized in `fonts.py` at project root
- Font path constants (Path objects) imported by widgets
- Fonts used: Geomini, HennyPenny, PlayfairDisplay, Righteous, WeatherIcons
- Example: `from fonts import FONT_GEOMINI`

**Screen Architecture:**

Screens are collections of widgets with a name:

```python
@dataclass
class Screen:
    name: str
    widgets: list[Widget]
    
    def get_partial_refresh_widgets(self) -> list[Widget]
    def get_all_widgets(self) -> list[Widget]
```

**Screen Registry:**
- Located in `screens/` directory
- Each screen defined in its own file: `<name>_screen.py`
- `screens/__init__.py` exports `AVAILABLE_SCREENS` dict and `get_screen()` function
- Add new screens by creating screen file and adding to registry

**Process Management:**

Communication between API server and display engine:

```
process/
├── commands.py         # TypedDict command definitions (SwitchScreenCommand, ShutdownCommand)
└── manager.py          # EngineProcessManager - process lifecycle management
```

**EngineProcessManager:**
- `start_engine()`: Spawn display engine process
- `stop_engine()`: Graceful shutdown with timeout
- `switch_screen(name)`: Send screen switch command via queue
- `is_alive()`: Check if engine process is running

**Command Queue:**
- `multiprocessing.Queue` for inter-process communication
- Commands: `{'type': 'switch_screen', 'screen_name': 'name'}`, `{'type': 'shutdown'}`
- Engine checks queue every second for responsive shutdown

## Key Components

**API Server (api/app.py):**
- `create_app()`: FastAPI application factory with lifespan management
- Endpoints:
  - `GET /`: API info and available screens
  - `GET /health`: Health check with engine status
  - `PUT /api/v1/screen`: Switch screen (with duplicate detection)
- Lifespan: Starts/stops EngineProcessManager on startup/shutdown

**Display Controller (display/display_controller.py):**

**Display class:**
- Main rendering engine managing refresh cycles
- `__init__(screen)`: Initialize hardware and state manager
- `run(command_queue)`: Main loop - checks commands every second, processes refresh on minute boundaries
- `full_refresh()`: Render all widgets to both channels, update state manager
- `partial_refresh()`: Region-specific black-only refresh for partial-refresh widgets
- `switch_screen(new_screen)`: Clear state, perform full refresh with new screen
- `cleanup()`: Release GPIO pins

**Main Loop Logic:**
```python
while True:
    # 1. Check command queue (non-blocking)
    if _process_command(queue):
        break  # Shutdown
    
    # 2. Check if new minute
    if current_minute != last_minute:
        _process_refresh(now)  # Full or partial
        last_minute = current_minute
    
    # 3. Sleep 1 second
    time.sleep(1.0)
```

**PartialStateManager (utils/):**
- Manages previous state for partial-refresh widgets
- `get_old_region(widget)`: Retrieve previous region image
- `update_state(widget, new_region)`: Store new region image
- `update_from_full_frame(full_frame)`: Extract and store all widget regions after full refresh
- `has_state()`: Check if any state is stored

**Refresh Strategy:**
1. Full refresh (every 15 min or first run):
   - Initialize display hardware
   - Render all widgets to full 800x480 image (black + red channels)
   - Send to e-paper controller
   - Extract and store regions for partial-refresh widgets
   - Put display to sleep

2. Partial refresh (every minute if widgets support it):
   - Check if screen has any partial-refresh widgets
   - If no partial widgets: skip refresh, sleep
   - If has partial widgets:
     - Initialize partial refresh mode
     - For each partial-refresh widget:
       - Get old region from state manager
       - Render widget to temp full image
       - Extract widget's region
       - Send old + new region buffers to e-paper (region-specific)
       - Update state manager with new region
     - Put display to sleep

**Settings (settings/settings.py):**
- Centralized configuration with Pydantic BaseSettings
- `BASE_DIR`: Project root path
- `FONTS_DIR`: Fonts directory path
- `DisplaySettings`: Width, height, full_refresh_interval
- `TimezoneSettings`: Name, UTC offset
- `WeatherSettings`: API key, location
- `APISettings`: Host, port (default: 0.0.0.0:8000)

## Adding New Features

**Adding a new screen:**
1. Create `screens/<name>_screen.py`
2. Define factory function `create_<name>_screen() -> Screen`
3. Instantiate widgets with their regions
4. Return `Screen(name="<name>", widgets=[...])`
5. Add to `AVAILABLE_SCREENS` dict in `screens/__init__.py`
6. Test via API: `curl -X PUT http://localhost:8000/api/v1/screen -d '{"screen": "<name>"}'`

**Screen Guidelines:**
- Full-screen widgets: Use region `WidgetRegion(0, 0, 800, 480)`
- Dashboard layouts: Divide 800x480 space into non-overlapping regions
- Partial refresh optimization: Only include if screen needs minute-by-minute updates
- No partial refresh widgets = refresh only every 15 minutes (saves e-paper wear)

**Adding a new widget:**
1. Create `widgets/<name>_widget.py`
2. Inherit from `Widget` and define `WidgetRegion` in `__init__()`
3. Implement `draw(black_draw, red_draw=None, **kwargs)` method
4. Optionally implement `draw_decorations()` and `draw_red_decorations()`
5. Set `supports_partial_refresh = True` if widget should update every minute (black-only)
6. Export in `widgets/__init__.py`
7. Add to screen(s) in `screens/` directory

**Widget Guidelines:**
- Draw at your widget's absolute coordinates (`self.region.x`, `self.region.y`)
- If widget owns a service, instantiate it in `__init__()` and fetch data in `draw()`
- Partial refresh widgets MUST work without red channel (`red_draw=None`)
- Use dynamic sizing/wrapping for text to prevent overflow
- Import fonts from `fonts.py`: `from fonts import FONT_GEOMINI`

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

**Target Platform:** Raspberry Pi (ARM)

**Architecture:**
- Main process: FastAPI server (manages API, spawns display engine)
- Child process: Display engine (hardware control, rendering loop)
- Communication: `multiprocessing.Queue` for commands

**Systemd Service:**
- Service file: `epaper-clock.service`
- Service user: `arkadip`
- Working directory: `/home/arkadip/e-paper`
- Virtual environment: `/home/arkadip/e-paper/.venv`
- Entry point: `main.py` (starts API server + display engine)
- Auto-restart on failure

**Process Management:**
- Graceful shutdown: API sends shutdown command, waits 10s, then terminates
- GPIO cleanup: Automatic on shutdown via `Display.cleanup()`
- Responsive shutdown: Commands checked every 1 second

**Environment Variables:**
- Set in `.env` file (copy from `.env.example`)
- `API_HOST`, `API_PORT`: API server bind address (default: 0.0.0.0:8000)
- `OPENWEATHER_API_KEY`, `LATITUDE`, `LONGITUDE`: Weather integration

## Code Documentation

All modules, classes, methods, and functions are documented with comprehensive Google-style docstrings:

**Core Display Modules:**
- `display/display_controller.py`: Display class, rendering engine
  - Main event loop with command processing
  - Full/partial refresh implementation
  - Hardware control (GPIO, SPI, e-paper driver)
  - State management and cleanup
- `display/display_main.py`: Process entry point
  - Spawned by EngineProcessManager
  - Configures logging for subprocess
  - Handles exceptions and cleanup

**API Modules:**
- `api/app.py`: FastAPI application factory
  - Lifespan management (startup/shutdown)
  - REST endpoints with Pydantic models
  - EngineProcessManager integration
  - Error handling and validation

**Process Management:**
- `process/manager.py`: EngineProcessManager class
  - Process lifecycle (start, stop, health check)
  - Command queue management
  - Graceful shutdown with timeout
- `process/commands.py`: TypedDict command definitions

**Screen Modules:**
- `screens/<name>_screen.py`: Screen factory functions
  - Widget instantiation with regions
  - Returns Screen dataclass
- `screens/__init__.py`: Screen registry and get_screen()

**Widget Modules:**
- `widgets/widget.py`: Base Widget class and WidgetRegion dataclass
  - Abstract interface with partial refresh contracts
  - Hardware constraints (e-paper dual-channel, polarity)
- `widgets/clock_widget.py`: Analog + digital clock with partial refresh
  - Smooth hour hand algorithm, coordinate system details
  - Constants documented (CX, CY, RADIUS, HOUR_LEN, MIN_LEN)
- `widgets/date_widget.py`: Day + date with scalloped borders
  - Typography strategy, decorative elements
- `widgets/weather_widget.py`: Current weather + 5-day forecast (400x240)
  - OpenWeatherMap integration, Weather Icons font mapping
- `widgets/todays_weather_widget.py`: Full-screen weather dashboard (800x480)
  - Current weather, stats bar, 24-hour temperature graph
  - Hourly forecast with weather icons
- `widgets/quote_widget.py`: Quote with adaptive font sizing
  - Dynamic sizing algorithm, Playfair Display typography

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

**Unit Tests:**
- `test_api.py`: API endpoint tests with mocked hardware
  - Tests all endpoints (/, /health, /api/v1/screen)
  - Validates response models
  - Checks duplicate screen handling
  - Run: `python test_api.py`

**Manual Testing (Development Machine):**
1. Run API tests: `python test_api.py`
2. Verify all endpoints work without hardware
3. Check for import errors and syntax issues

**Manual Testing (Raspberry Pi):**
1. Start API server: `uv run python main.py`
2. Check initial screen renders correctly
3. Test screen switching:
   ```bash
   curl -X PUT http://localhost:8000/api/v1/screen \
        -H "Content-Type: application/json" \
        -d '{"screen": "todays_weather"}'
   ```
4. Verify screen switches with full refresh
5. Test duplicate switch returns "Already on" message
6. Watch logs for refresh cycles:
   - Full refresh every 15 minutes for screens with no partial widgets
   - Full + partial refresh for screens with partial widgets
7. Test graceful shutdown: `Ctrl+C` should cleanup within 1-2 seconds
8. Check for GPIO errors in logs

**Standalone Mode Testing:**
1. Run without API: `uv run python main_standalone.py`
2. Verify single-screen operation
3. Test Ctrl+C shutdown

**Monitoring:**
```bash
# Watch logs
journalctl -u epaper-clock -f

# Check process status
systemctl status epaper-clock

# View API status
curl http://localhost:8000/health
```

## Directory Structure

```
e-paper/
├── main.py                          # Entry point: FastAPI server + display engine
├── main_standalone.py               # Entry point: Standalone display (no API)
├── test_api.py                      # API tests with mocked hardware
├── fonts.py                         # Centralized font path constants
├── .env                             # Environment configuration
├── .env.example                     # Environment template
├── epaper-clock.service             # Systemd service file
├── CLAUDE.md                        # This file
│
├── api/                             # FastAPI REST API
│   ├── __init__.py
│   └── app.py                       # Application factory, endpoints, lifespan
│
├── display/                         # Display engine (process isolation)
│   ├── __init__.py                  # Exports Display class
│   ├── display_controller.py       # Core rendering engine
│   └── display_main.py              # Process entry point
│
├── process/                         # Process management
│   ├── __init__.py
│   ├── manager.py                   # EngineProcessManager
│   └── commands.py                  # Command TypedDicts
│
├── screens/                         # Screen definitions
│   ├── __init__.py                  # Screen registry (AVAILABLE_SCREENS, get_screen)
│   ├── datetime_weather_forecast_screen.py  # 4-widget dashboard
│   └── todays_weather_screen.py     # Full-screen weather
│
├── widgets/                         # Widget implementations
│   ├── __init__.py
│   ├── widget.py                    # Abstract base class
│   ├── clock_widget.py              # Analog + digital clock (partial refresh)
│   ├── date_widget.py               # Day + date
│   ├── weather_widget.py            # 5-day forecast (400x240)
│   ├── todays_weather_widget.py     # Full-screen weather dashboard
│   └── quote_widget.py              # Quote of the day
│
├── services/                        # Data services
│   ├── quote/
│   │   ├── __init__.py
│   │   ├── quote_service.py         # Abstract QuoteService
│   │   └── zenquotes_service.py     # ZenQuotes implementation
│   └── weather/
│       ├── __init__.py
│       ├── weather_service.py       # Abstract WeatherService
│       └── openweathermap_service.py  # OpenWeatherMap implementation
│
├── utils/                           # Utilities
│   ├── __init__.py
│   ├── datetime_util.py             # Timezone-aware datetime
│   ├── screen.py                    # Screen dataclass
│   ├── log.py                       # Logging configuration
│   └── partial_state_manager.py     # Partial refresh state tracking
│
├── settings/                        # Configuration
│   ├── __init__.py
│   └── settings.py                  # Pydantic settings (BASE_DIR, FONTS_DIR, etc.)
│
├── fonts/                           # Font files
│   ├── Geomini-VariableFont_wght.ttf
│   ├── PlayfairDisplay-*.ttf
│   ├── HennyPenny-Regular.ttf
│   ├── Righteous-Regular.ttf
│   └── weathericons-regular-webfont.ttf
│
└── lib/                             # External libraries
    └── waveshare_epd/               # Waveshare e-paper driver (read-only)
        └── epd7in5b_V2.py           # Hardware driver
```
