import axios from 'axios';

const getBaseURL = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (['localhost', '127.0.0.1'].includes(host)) {
      return '/api';
    }

    if (host.includes('tru-sight-ai') || host.includes('true-sight-ai')) {
      return 'https://true-sight-ai.onrender.com/api';
    }
  }

  return 'https://true-sight-ai.onrender.com/api';
};

const api = axios.create({
  baseURL: getBaseURL(),
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
