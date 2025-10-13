/**
 * API client service with auth token management
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Axios instance configured for DDMS API
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Include cookies for refresh tokens
});

/**
 * Request interceptor to add auth token
 */
apiClient.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor to handle token refresh
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // If 401 and not already retried, attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        // Attempt to refresh token
        const refreshResponse = await axios.post(
          `${API_BASE_URL}/api/auth/refresh`,
          {},
          { withCredentials: true }
        );

        const newToken = refreshResponse.data.access_token;
        localStorage.setItem('access_token', newToken);

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

/**
 * API service methods
 */
export const api = {
  // Auth
  login: (username: string, password: string) =>
    apiClient.post('/api/auth/login', { username, password }),

  logout: () => apiClient.post('/api/auth/logout'),

  changePassword: (oldPassword: string, newPassword: string) =>
    apiClient.post('/api/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    }),

  // Devices
  getDevices: () => apiClient.get('/api/devices'),

  getDevice: (deviceId: string) => apiClient.get(`/api/devices/${deviceId}`),

  createDevice: (device: any) => apiClient.post('/api/devices', device),

  updateDevice: (deviceId: string, device: any) =>
    apiClient.put(`/api/devices/${deviceId}`, device),

  deleteDevice: (deviceId: string, keepData: boolean = false) =>
    apiClient.delete(`/api/devices/${deviceId}`, { params: { keep_data: keepData } }),

  getLatestReading: (deviceId: string) => apiClient.get(`/api/devices/${deviceId}/latest`),

  // Readings
  getReadings: (deviceId: string, params?: any) =>
    apiClient.get(`/api/readings/${deviceId}`, { params }),

  // Users
  getUsers: () => apiClient.get('/api/users'),

  createUser: (user: any) => apiClient.post('/api/users', user),

  deleteUser: (userId: string) => apiClient.delete(`/api/users/${userId}`),

  // Groups
  getGroups: () => apiClient.get('/api/groups'),

  getGroup: (groupId: string) => apiClient.get(`/api/groups/${groupId}`),

  createGroup: (group: any) => apiClient.post('/api/groups', group),

  updateGroup: (groupId: string, group: any) => apiClient.put(`/api/groups/${groupId}`, group),

  deleteGroup: (groupId: string) => apiClient.delete(`/api/groups/${groupId}`),

  // System
  getHealth: () => apiClient.get('/api/system/health'),

  getConfig: () => apiClient.get('/api/system/config'),

  updateConfig: (config: any) => apiClient.put('/api/system/config', config),

  // Export
  exportDeviceData: (deviceId: string, params?: any) =>
    apiClient.get(`/api/export/device/${deviceId}`, {
      params,
      responseType: 'blob',
    }),

  exportGroupData: (groupId: string, params?: any) =>
    apiClient.get(`/api/export/group/${groupId}`, {
      params,
      responseType: 'blob',
    }),
};

export default apiClient;
