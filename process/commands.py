"""Command definitions for inter-process communication.

Commands are sent from the API server (main process) to the display engine
(child process) via a multiprocessing.Queue. Each command is a dictionary
with a 'type' field and optional 'data' payload.

Command Types:
    - switch_screen: Change to a different screen layout
    - shutdown: Gracefully stop the engine process

Example:
    command_queue.put({
        'type': 'switch_screen',
        'screen_name': 'todays_weather'
    })
"""

from typing import Literal, TypedDict


class SwitchScreenCommand(TypedDict):
    """Command to switch to a different screen.

    Attributes:
        type: Always 'switch_screen'
        screen_name: Name of screen from AVAILABLE_SCREENS registry
    """

    type: Literal["switch_screen"]
    screen_name: str


class ShutdownCommand(TypedDict):
    """Command to shutdown the engine process.

    Attributes:
        type: Always 'shutdown'
    """

    type: Literal["shutdown"]


# Union type for all commands
Command = SwitchScreenCommand | ShutdownCommand
