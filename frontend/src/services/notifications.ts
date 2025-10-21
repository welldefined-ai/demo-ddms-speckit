/**
 * Notification service for managing in-app notifications
 *
 * Features:
 * - Fetch notifications with pagination
 * - Mark notifications as read
 * - Dismiss notifications
 * - Real-time notification updates via SSE
 */

import apiClient from './api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAY = 3000; // 3 seconds

// Types
export type NotificationType = 'device_disconnect' | 'device_alert' | 'system';
export type NotificationSeverity = 'info' | 'warning' | 'error' | 'critical';

export interface Notification {
  id: string;
  type: NotificationType;
  severity: NotificationSeverity;
  title: string;
  message: string;
  device_id?: string;
  metadata?: Record<string, any>;
  read_at?: string;
  dismissed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface NotificationStreamData {
  unread_count: number;
  notifications: Notification[];
}

export type SSEConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

// API Functions
export const notificationApi = {
  /**
   * Fetch notifications for the current user
   */
  getNotifications: (
    unreadOnly: boolean = false,
    limit: number = 50,
    offset: number = 0
  ): Promise<NotificationListResponse> => {
    return apiClient
      .get('/api/notifications', {
        params: { unread_only: unreadOnly, limit, offset },
      })
      .then((response) => response.data);
  },

  /**
   * Get count of unread notifications
   */
  getUnreadCount: (): Promise<number> => {
    return apiClient
      .get('/api/notifications/unread-count')
      .then((response) => response.data.unread_count);
  },

  /**
   * Mark a notification as read
   */
  markAsRead: (notificationId: string): Promise<Notification> => {
    return apiClient
      .put(`/api/notifications/${notificationId}/read`)
      .then((response) => response.data);
  },

  /**
   * Mark all notifications as read
   */
  markAllAsRead: (): Promise<{ message: string }> => {
    return apiClient.put('/api/notifications/read-all').then((response) => response.data);
  },

  /**
   * Dismiss a notification
   */
  dismiss: (notificationId: string): Promise<{ message: string }> => {
    return apiClient
      .delete(`/api/notifications/${notificationId}`)
      .then((response) => response.data);
  },
};

// SSE Client for real-time notifications
export interface NotificationSSEClientOptions {
  onMessage: (data: NotificationStreamData) => void;
  onError?: (error: Event) => void;
  onStateChange?: (state: SSEConnectionState) => void;
}

export class NotificationSSEClient {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private reconnectTimeout: number | null = null;
  private options: NotificationSSEClientOptions;
  private connectionState: SSEConnectionState = 'disconnected';

  constructor(options: NotificationSSEClientOptions) {
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
      // EventSource doesn't support custom headers, so we pass token as query param
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.error('No access token found for notification SSE');
        this.setState('error');
        return;
      }

      const url = `${API_BASE_URL}/api/notifications/stream?token=${encodeURIComponent(token)}`;
      this.eventSource = new EventSource(url);

      this.eventSource.onopen = () => {
        console.log('Notification SSE connection established');
        this.setState('connected');
        this.reconnectAttempts = 0;
      };

      this.eventSource.onmessage = (event: MessageEvent) => {
        try {
          const data: NotificationStreamData = JSON.parse(event.data);
          this.options.onMessage(data);
        } catch (error) {
          console.error('Failed to parse notification SSE message:', error);
        }
      };

      this.eventSource.onerror = (error: Event) => {
        console.error('Notification SSE connection error:', error);
        this.setState('error');

        if (this.options.onError) {
          this.options.onError(error);
        }

        // Attempt to reconnect
        this.handleReconnect();
      };
    } catch (error) {
      console.error('Failed to create notification EventSource:', error);
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
        `Attempting to reconnect to notification stream (${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`
      );

      this.reconnectTimeout = window.setTimeout(() => {
        this.connect();
      }, RECONNECT_DELAY);
    } else {
      console.log('Max notification reconnection attempts reached.');
      this.setState('disconnected');
    }
  }

  /**
   * Disconnect from SSE
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
