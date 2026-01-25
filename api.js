import axios from 'axios';
import { toast } from 'react-toastify';
import { auth } from './firebase';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor to attach Firebase ID token
api.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'Request failed';
    toast.error(message, { theme: 'dark' });
    return Promise.reject(error);
  }
);

export const fetchAuditLogs = async () => {
  const response = await api.get('/admin/audit-logs');
  return response.data;
};

export const fetchAttackLogs = async () => {
  const response = await api.get('/admin/attack-logs');
  return response.data;
};

export const fetchAttackStats = async () => {
  const response = await api.get('/admin/attack-stats');
  return response.data;
};

export const checkHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};