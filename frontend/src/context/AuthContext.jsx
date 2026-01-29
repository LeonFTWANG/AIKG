import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 初始化拦截器
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response && error.response.status === 401) {
          logout();
        }
        return Promise.reject(error);
      }
    );

    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));

        // 检查是否过期
        if (payload.exp && payload.exp * 1000 < Date.now()) {
          throw new Error('Token expired');
        }

        setUser({ username: payload.sub });
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } catch (e) {
        console.warn("Invalid or expired token", e);
        logout();
      }
    }
    setLoading(false);

    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, [token]);

  const login = async (username, password) => {
    try {
      const response = await axios.post('http://localhost:8000/api/auth/login', {
        username,
        password
      }, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      const { access_token } = response.data;
      setToken(access_token);
      localStorage.setItem('token', access_token);
      return true;
    } catch (error) {
      console.error("Login failed", error);
      throw error;
    }
  };

  const register = async (username, password) => {
    try {
      await axios.post('http://localhost:8000/api/auth/register', {
        username,
        password
      });
      return true;
    } catch (error) {
      console.error("Registration failed", error);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
