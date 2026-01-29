import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import GraphPage from './pages/GraphPage';
import SearchPage from './pages/SearchPage';
import LabsPage from './pages/LabsPage';
import ChatPage from './pages/ChatPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import { AuthProvider } from './context/AuthContext';
import './App.css';

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <AuthProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/graph" element={<GraphPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/labs" element={<LabsPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Routes>
          </Layout>
        </Router>
      </AuthProvider>
    </ConfigProvider>
  );
}

export default App;

