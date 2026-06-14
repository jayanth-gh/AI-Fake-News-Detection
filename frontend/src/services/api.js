import axios from 'axios';

const isLocalDev = typeof window !== 'undefined' && ['localhost', '127.0.0.1'].includes(window.location.hostname);
const fallbackBaseURL = isLocalDev ? '/api' : 'https://true-sight-ai.onrender.com/api';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || fallbackBaseURL,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default api;
