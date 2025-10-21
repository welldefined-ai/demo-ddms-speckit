/**
 * Browser Push Notifications utility
 *
 * Handles Web Notifications API for desktop browser notifications
 */

export type NotificationPermissionStatus = 'default' | 'granted' | 'denied';

/**
 * Check if browser supports notifications
 */
export const isNotificationSupported = (): boolean => {
  return 'Notification' in window;
};

/**
 * Get current notification permission status
 */
export const getNotificationPermission = (): NotificationPermissionStatus => {
  if (!isNotificationSupported()) {
    return 'denied';
  }
  return Notification.permission as NotificationPermissionStatus;
};

/**
 * Request notification permission from user
 */
export const requestNotificationPermission = async (): Promise<NotificationPermissionStatus> => {
  if (!isNotificationSupported()) {
    console.warn('Browser does not support notifications');
    return 'denied';
  }

  try {
    const permission = await Notification.requestPermission();
    return permission as NotificationPermissionStatus;
  } catch (error) {
    console.error('Error requesting notification permission:', error);
    return 'denied';
  }
};

export interface BrowserNotificationOptions {
  title: string;
  body: string;
  icon?: string;
  badge?: string;
  tag?: string;
  data?: any;
  requireInteraction?: boolean;
  silent?: boolean;
}

/**
 * Show a browser notification
 */
export const showBrowserNotification = (
  options: BrowserNotificationOptions
): Notification | null => {
  if (!isNotificationSupported()) {
    console.warn('Browser does not support notifications');
    return null;
  }

  if (Notification.permission !== 'granted') {
    console.warn('Notification permission not granted');
    return null;
  }

  try {
    const notification = new Notification(options.title, {
      body: options.body,
      icon: options.icon || '/notification-icon.png',
      badge: options.badge || '/notification-badge.png',
      tag: options.tag,
      data: options.data,
      requireInteraction: options.requireInteraction || false,
      silent: options.silent || false,
    });

    // Auto-close after 10 seconds if not require interaction
    if (!options.requireInteraction) {
      setTimeout(() => {
        notification.close();
      }, 10000);
    }

    return notification;
  } catch (error) {
    console.error('Error showing browser notification:', error);
    return null;
  }
};

/**
 * Show device disconnect notification
 */
export const showDeviceDisconnectNotification = (
  deviceName: string,
  deviceIp: string,
  onClick?: () => void
): Notification | null => {
  const notification = showBrowserNotification({
    title: `Device Disconnected: ${deviceName}`,
    body: `Device '${deviceName}' (${deviceIp}) has failed to respond after 3 retry attempts.`,
    tag: `device-disconnect-${deviceName}`,
    requireInteraction: true,
    data: {
      type: 'device_disconnect',
      deviceName,
      deviceIp,
    },
  });

  if (notification && onClick) {
    notification.onclick = () => {
      window.focus();
      onClick();
      notification.close();
    };
  }

  return notification;
};

/**
 * Check if notification permission should be requested
 * Only request once per session to avoid annoying users
 */
export const shouldRequestPermission = (): boolean => {
  const permission = getNotificationPermission();
  const hasAskedThisSession = sessionStorage.getItem('notification-permission-asked');

  return (
    isNotificationSupported() &&
    permission === 'default' &&
    !hasAskedThisSession
  );
};

/**
 * Mark that we've asked for permission this session
 */
export const markPermissionAsked = (): void => {
  sessionStorage.setItem('notification-permission-asked', 'true');
};
