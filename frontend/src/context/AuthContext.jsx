import React, { createContext, useState, useEffect } from 'react';
import api from '../services/api';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');
    if (token && username) {
      setUser({ token, username });
    }
    setLoading(false);
  }, []);

  // ✅ LOGIN (fix endpoint also)
  const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const res = await api.post('/auth/login', formData, {   // ✅ fixed endpoint
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });

    localStorage.setItem('token', res.data.access_token);
    localStorage.setItem('username', username);

    setUser({ token: res.data.access_token, username });
  };

  // ✅ REGISTER (FIXED)
  const register = async (username, email, password) => {
    await api.post('/auth/register', {
      username,
      email,     // ✅ REQUIRED
      password,
    });

    // Auto login after register
    return login(username, password);
  };

  // ✅ LOGOUT
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setUser(null);
  };

  if (loading) return <div>Loading...</div>;

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};