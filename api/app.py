"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from process import EngineProcessManager
from screens import AVAILABLE_SCREENS, DEFAULT_SCREEN

logger = logging.getLogger(__name__)


class ScreenSwitchRequest(BaseModel):
    """Request body for switching screens."""

    screen: str


class ScreenSwitchResponse(BaseModel):
    """Response for screen switch operation."""

    success: bool
    screen: str
    message: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    engine_running: bool
    current_screen: str


class InfoResponse(BaseModel):
    """API info response."""

    name: str
    version: str
    available_screens: list[str]
    current_screen: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Starting engine process...")
    manager = EngineProcessManager(initial_screen=DEFAULT_SCREEN)
    manager.start_engine()
    app.state.engine_manager = manager
    app.state.current_screen = DEFAULT_SCREEN

    yield

    # Shutdown
    logger.info("Stopping engine process...")
    manager.stop_engine()


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI app instance
    """
    app = FastAPI(
        title="E-Paper Display API",
        description="Control e-paper display screens via REST API",
        version="1.0.0",
        lifespan=lifespan,
    )

    @app.get("/", response_model=InfoResponse)
    def root():
        """Get API information."""
        return InfoResponse(
            name="E-Paper Display API",
            version="1.0.0",
            available_screens=list(AVAILABLE_SCREENS.keys()),
            current_screen=app.state.current_screen,
        )

    @app.get("/health", response_model=HealthResponse)
    def health():
        """Health check endpoint."""
        manager: EngineProcessManager = app.state.engine_manager
        return HealthResponse(
            status="healthy",
            engine_running=manager.is_alive(),
            current_screen=app.state.current_screen,
        )

    @app.put("/api/v1/screen", response_model=ScreenSwitchResponse)
    def switch_screen(request: ScreenSwitchRequest):
        """Switch to a different screen.

        Args:
            request: Screen name to switch to

        Returns:
            Success response with new screen name

        Raises:
            HTTPException: If screen name invalid or engine not running
        """
        if request.screen not in AVAILABLE_SCREENS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown screen '{request.screen}'. Available: {list(AVAILABLE_SCREENS.keys())}",
            )

        manager: EngineProcessManager = app.state.engine_manager

        if not manager.is_alive():
            raise HTTPException(
                status_code=503, detail="Engine process is not running"
            )

        try:
            manager.switch_screen(request.screen)
            app.state.current_screen = request.screen

            return ScreenSwitchResponse(
                success=True,
                screen=request.screen,
                message=f"Switched to '{request.screen}' screen",
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to switch screen: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to switch screen: {str(e)}"
            )

    return app
