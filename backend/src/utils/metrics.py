"""
Prometheus metrics exporter
"""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from typing import Optional

# Create a custom registry for better control
registry = CollectorRegistry()

# API Request Metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

api_request_duration_seconds = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    registry=registry,
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Device Metrics
device_readings_total = Counter(
    'device_readings_total',
    'Total number of device readings collected',
    ['device_id', 'device_name'],
    registry=registry
)

device_errors_total = Counter(
    'device_errors_total',
    'Total number of device collection errors',
    ['device_id', 'device_name', 'error_type'],
    registry=registry
)

devices_online = Gauge(
    'devices_online',
    'Number of devices currently online',
    registry=registry
)

devices_total = Gauge(
    'devices_total',
    'Total number of configured devices',
    registry=registry
)

# Database Metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    registry=registry
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    registry=registry,
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0)
)

# Authentication Metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total number of authentication attempts',
    ['status'],
    registry=registry
)

active_users = Gauge(
    'active_users',
    'Number of active user sessions',
    registry=registry
)

# System Health Metrics
system_health = Gauge(
    'system_health',
    'Overall system health status (1=healthy, 0=unhealthy)',
    registry=registry
)


def get_metrics() -> bytes:
    """
    Get Prometheus-formatted metrics

    Returns:
        Bytes containing Prometheus-formatted metrics
    """
    return generate_latest(registry)


def record_api_request(method: str, endpoint: str, status: int, duration: float) -> None:
    """
    Record an API request in metrics

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        status: HTTP status code
        duration: Request duration in seconds
    """
    api_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_device_reading(device_id: str, device_name: str) -> None:
    """
    Record a successful device reading

    Args:
        device_id: Device UUID
        device_name: Device name
    """
    device_readings_total.labels(device_id=device_id, device_name=device_name).inc()


def record_device_error(device_id: str, device_name: str, error_type: str) -> None:
    """
    Record a device collection error

    Args:
        device_id: Device UUID
        device_name: Device name
        error_type: Type of error (connection, timeout, etc.)
    """
    device_errors_total.labels(device_id=device_id, device_name=device_name, error_type=error_type).inc()


def update_device_counts(online: int, total: int) -> None:
    """
    Update device count metrics

    Args:
        online: Number of online devices
        total: Total number of devices
    """
    devices_online.set(online)
    devices_total.set(total)


def record_auth_attempt(success: bool) -> None:
    """
    Record an authentication attempt

    Args:
        success: Whether the authentication was successful
    """
    status = "success" if success else "failure"
    auth_attempts_total.labels(status=status).inc()


def set_system_health(healthy: bool) -> None:
    """
    Set overall system health status

    Args:
        healthy: Whether the system is healthy
    """
    system_health.set(1 if healthy else 0)
