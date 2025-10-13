/**
 * Server-Sent Events (SSE) client with auto-reconnect functionality
 *
 * Features:
 * - Automatic reconnection (up to 3 attempts)
 * - Fallback to polling if SSE fails
 * - Connection state management
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAY = 3000; // 3 seconds
const POLLING_INTERVAL = 5000; // 5 seconds fallback polling

export type DeviceReading = {
  device_id: string;
  device_name: string;
  unit: string;
  timestamp: string;
  value: number;
  status: 'normal' | 'warning' | 'critical';
};

export type SSEConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface SSEClientOptions {
  onMessage: (data: DeviceReading[]) => void;
  onError?: (error: Event) => void;
  onStateChange?: (state: SSEConnectionState) => void;
}

export class SSEClient {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private reconnectTimeout: number | null = null;
  private pollingInterval: number | null = null;
  private options: SSEClientOptions;
  private connectionState: SSEConnectionState = 'disconnected';

  constructor(options: SSEClientOptions) {
    this.options = options;
  }

  /**
   * Start the SSE connection
   */
  connect(): void {
    if (this.eventSource) {
      this.disconnect();
    }

    this.setState('connecting');

    try {
      const url = `${API_BASE_URL}/api/devices/stream`;
      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        console.log('SSE connection established');
        this.setState('connected');
        this.reconnectAttempts = 0;
      };

      this.eventSource.onmessage = (event: MessageEvent) => {
        try {
          const data: DeviceReading[] = JSON.parse(event.data);
          this.options.onMessage(data);
        } catch (error) {
          console.error('Failed to parse SSE message:', error);
        }
      };

      this.eventSource.onerror = (error: Event) => {
        console.error('SSE connection error:', error);
        this.setState('error');

        if (this.options.onError) {
          this.options.onError(error);
        }

        // Attempt to reconnect
        this.handleReconnect();
      };
    } catch (error) {
      console.error('Failed to create EventSource:', error);
      this.setState('error');
      this.handleReconnect();
    }
  }

  /**
   * Handle reconnection logic
   */
  private handleReconnect(): void {
    this.disconnect();

    if (this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
      this.reconnectAttempts++;
      console.log(
        `Attempting to reconnect (${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`
      );

      this.reconnectTimeout = window.setTimeout(() => {
        this.connect();
      }, RECONNECT_DELAY);
    } else {
      console.log('Max reconnection attempts reached. Falling back to polling.');
      this.fallbackToPolling();
    }
  }

  /**
   * Fallback to HTTP polling if SSE fails
   */
  private fallbackToPolling(): void {
    if (this.pollingInterval) {
      return; // Already polling
    }

    console.log('Starting polling fallback');
    this.setState('connected'); // Consider polling as connected

    // Immediate fetch
    this.fetchDeviceReadings();

    // Start polling interval
    this.pollingInterval = window.setInterval(() => {
      this.fetchDeviceReadings();
    }, POLLING_INTERVAL);
  }

  /**
   * Fetch device readings via HTTP (for polling fallback)
   */
  private async fetchDeviceReadings(): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/devices`);
      if (response.ok) {
        const data = await response.json();
        this.options.onMessage(data);
      }
    } catch (error) {
      console.error('Polling fetch error:', error);
    }
  }

  /**
   * Disconnect from SSE or stop polling
   */
  disconnect(): void {
    // Close EventSource
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    // Clear reconnect timeout
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Clear polling interval
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }

    this.setState('disconnected');
  }

  /**
   * Update connection state
   */
  private setState(state: SSEConnectionState): void {
    this.connectionState = state;
    if (this.options.onStateChange) {
      this.options.onStateChange(state);
    }
  }

  /**
   * Get current connection state
   */
  getState(): SSEConnectionState {
    return this.connectionState;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connectionState === 'connected';
  }
}
