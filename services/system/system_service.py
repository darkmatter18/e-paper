"""System information service.

Provides WiFi signal strength and CPU temperature for Raspberry Pi.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SystemInfo:
    """System information data.

    Attributes:
        wifi_strength: WiFi signal strength in dBm (-100 to 0, closer to 0 is better)
        cpu_temp: CPU temperature in degrees Celsius
    """

    wifi_strength: int  # dBm
    cpu_temp: float  # Celsius


class SystemService:
    """Service for reading system information on Raspberry Pi."""

    THERMAL_PATH = Path("/sys/class/thermal/thermal_zone0/temp")
    WIRELESS_PATH = Path("/proc/net/wireless")

    @staticmethod
    def get_cpu_temp() -> float:
        """Read CPU temperature from system.

        Returns:
            Temperature in degrees Celsius

        Note:
            Returns 0.0 if reading fails (not on Raspberry Pi)
        """
        try:
            temp_raw = SystemService.THERMAL_PATH.read_text().strip()
            # Temperature is in millidegrees, convert to degrees
            return int(temp_raw) / 1000.0
        except Exception as e:
            logger.warning(f"Failed to read CPU temperature: {e}")
            return 0.0

    @staticmethod
    def get_wifi_strength() -> int:
        """Read WiFi signal strength from system.

        Returns:
            Signal strength in dBm (-100 to 0)

        Note:
            Returns -100 (worst) if reading fails
        """
        try:
            lines = SystemService.WIRELESS_PATH.read_text().strip().split("\n")
            # Skip header lines
            for line in lines[2:]:
                # Parse wireless stats line
                # Format: "wlan0: 0000   70.  -40.  -256        0      0      0      0      0        0"
                parts = line.split()
                if len(parts) >= 4:
                    # Signal level is typically the 4th column (index 3)
                    signal_str = parts[3].rstrip(".")
                    return int(signal_str)
        except Exception as e:
            logger.warning(f"Failed to read WiFi strength: {e}")

        return -100  # Worst possible signal

    @classmethod
    def get_system_info(cls) -> SystemInfo:
        """Get current system information.

        Returns:
            SystemInfo with WiFi strength and CPU temperature
        """
        return SystemInfo(
            wifi_strength=cls.get_wifi_strength(), cpu_temp=cls.get_cpu_temp()
        )
