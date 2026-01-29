import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Layout as AntLayout,
  Menu,
  Typography,
  Space,
  Button,
} from 'antd';
import { useAuth } from '../context/AuthContext';
import {
  HomeOutlined,
  ApartmentOutlined,
  SearchOutlined,
  ExperimentOutlined,
  MessageOutlined,
  GithubOutlined,
} from '@ant-design/icons';

const { Header, Content, Footer } = AntLayout;
const { Title } = Typography;

const Layout = ({ children }) => {
  const location = useLocation();
  const [current, setCurrent] = useState(location.pathname);
  const { user, logout } = useAuth();

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: '/graph',
      icon: <ApartmentOutlined />,
      label: <Link to="/graph">知识图谱</Link>,
    },
    {
      key: '/search',
      icon: <SearchOutlined />,
      label: <Link to="/search">搜索</Link>,
    },
    {
      key: '/labs',
      icon: <ExperimentOutlined />,
      label: <Link to="/labs">靶场</Link>,
    },
    {
      key: '/chat',
      icon: <MessageOutlined />,
      label: <Link to="/chat">AI问答</Link>,
    },
  ];

  return (
    <AntLayout className="app-container">
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        background: '#001529',
        padding: '0 20px'
      }}>
        <Space size="large" style={{ flex: 1 }}>
          <Title level={3} style={{
            color: 'white',
            margin: 0,
            fontSize: '20px'
          }}>
            🛡️ AI安全知识图谱
          </Title>
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[current]}
            items={menuItems}
            style={{
              flex: 1,
              minWidth: 0,
              background: 'transparent'
            }}
            onClick={(e) => setCurrent(e.key)}
          />
        </Space>

        <Space>
          {user ? (
            <>
              <span style={{ color: 'white' }}>你好, {user.username}</span>
              <Button type="link" onClick={logout} style={{ color: '#1890ff' }}>退出</Button>
            </>
          ) : (
            <Link to="/login" style={{ color: 'white' }}>登录</Link>
          )}
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            style={{ color: 'white', fontSize: '20px', marginLeft: 16 }}
          >
            <GithubOutlined />
          </a>
        </Space>
      </Header>

      <Content className="page-content">
        {children}
      </Content>

      <Footer style={{ textAlign: 'center', background: '#f0f2f5' }}>
        AI Security Knowledge Graph ©2024 |
        基于 Neo4j + Dify + LLM 构建的智能安全学习平台
      </Footer>
    </AntLayout>
  );
};

export default Layout;

