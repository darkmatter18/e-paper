"""Test script for FastAPI endpoints (without hardware).

This script tests the API endpoints without actually starting the display engine.
Useful for verifying API structure before deployment to Raspberry Pi.
"""

from dotenv import load_dotenv
from fastapi.testclient import TestClient

load_dotenv()

# Mock the engine process for testing
import sys
from unittest.mock import Mock, patch

# Mock hardware modules
sys.modules["lib.waveshare_epd"] = Mock()
sys.modules["lib.waveshare_epd.epd7in5b_V2"] = Mock()

# Now import the app
from api import create_app


def test_api():
    """Test API endpoints."""
    print("=" * 60)
    print("Testing FastAPI Endpoints (Mock Mode)")
    print("=" * 60)

    # Patch EngineProcessManager to not actually start the process
    with patch("api.app.EngineProcessManager") as MockManager:
        # Setup mock manager
        mock_manager = Mock()
        mock_manager.is_alive.return_value = True
        mock_manager.current_screen = "datetime_weather_forecast"
        MockManager.return_value = mock_manager

        # Create app
        app = create_app()
        client = TestClient(app)

        # Test 1: Root endpoint
        print("\n1. Testing GET /")
        response = client.get("/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        assert response.status_code == 200
        assert "available_screens" in response.json()
        print("   ✓ Root endpoint works")

        # Test 2: Health endpoint
        print("\n2. Testing GET /health")
        response = client.get("/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        assert response.status_code == 200
        print("   ✓ Health endpoint works")

        # Test 3: Switch screen (valid)
        print("\n3. Testing PUT /api/v1/screen (valid screen)")
        response = client.put(
            "/api/v1/screen", json={"screen": "todays_weather"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        assert response.status_code == 200
        assert response.json()["screen"] == "todays_weather"
        print("   ✓ Screen switch works")

        # Test 4: Switch screen (invalid)
        print("\n4. Testing PUT /api/v1/screen (invalid screen)")
        response = client.put(
            "/api/v1/screen", json={"screen": "nonexistent"}
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        assert response.status_code == 400
        print("   ✓ Invalid screen properly rejected")

        # Test 5: Available screens
        print("\n5. Checking available screens")
        response = client.get("/")
        screens = response.json()["available_screens"]
        print(f"   Available: {screens}")
        assert "datetime_weather_forecast" in screens
        assert "todays_weather" in screens
        print("   ✓ All screens registered")

    print("\n" + "=" * 60)
    print("✅ All API tests passed!")
    print("\nAPI Endpoints:")
    print("  GET  /              - API info & available screens")
    print("  GET  /health        - Health check")
    print("  PUT  /api/v1/screen - Switch screen")
    print("\nExample:")
    print('  curl -X PUT http://localhost:8000/api/v1/screen \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"screen": "todays_weather"}\'')
    print("=" * 60)


if __name__ == "__main__":
    test_api()
