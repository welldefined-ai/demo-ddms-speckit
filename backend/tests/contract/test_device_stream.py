"""
Contract tests for SSE device stream endpoint

Tests the Server-Sent Events streaming functionality
"""
import pytest
from fastapi.testclient import TestClient
import time
import json

from src.main import app

client = TestClient(app)


class TestDeviceStreamSSE:
    """Test GET /api/devices/stream (SSE) endpoint"""

    def test_stream_endpoint_exists(self):
        """Test that SSE stream endpoint exists and returns correct headers"""
        response = client.get("/api/devices/stream", stream=True)

        # SSE endpoints return 200 and stream data
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        assert response.headers.get("cache-control") == "no-cache"
        assert response.headers.get("connection") == "keep-alive"

    def test_stream_sends_events(self):
        """Test that stream sends events in SSE format"""
        with client.stream("GET", "/api/devices/stream") as response:
            assert response.status_code == 200

            # Read first few events (with timeout)
            events = []
            start_time = time.time()

            for line in response.iter_lines():
                if time.time() - start_time > 5:  # 5 second timeout
                    break

                if line.startswith("data:"):
                    data = line[5:].strip()  # Remove "data:" prefix
                    events.append(data)

                    if len(events) >= 2:  # Get at least 2 events
                        break

            # Verify we got events
            assert len(events) > 0

    def test_stream_event_format(self):
        """Test that stream events are valid JSON"""
        with client.stream("GET", "/api/devices/stream") as response:
            assert response.status_code == 200

            # Read first event
            for line in response.iter_lines():
                if line.startswith("data:"):
                    data = line[5:].strip()

                    # Should be valid JSON
                    try:
                        event_data = json.loads(data)
                        assert isinstance(event_data, (dict, list))
                        break
                    except json.JSONDecodeError:
                        pytest.fail(f"Invalid JSON in SSE event: {data}")

    def test_stream_reconnection_support(self):
        """Test that stream supports reconnection with Last-Event-ID"""
        headers = {"Last-Event-ID": "12345"}
        response = client.get("/api/devices/stream", headers=headers, stream=True)

        # Should accept the header (implementation may use it for replay)
        assert response.status_code == 200
