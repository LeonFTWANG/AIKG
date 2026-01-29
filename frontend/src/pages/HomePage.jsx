import React, { useState, useEffect } from 'react';
import { Typography, Card, Row, Col, Statistic, Button } from 'antd';
import {
  SafetyCertificateOutlined,
  BugOutlined,
  ExperimentOutlined,
  ReadOutlined,
  ArrowRightOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import axios from 'axios';

const { Title, Paragraph } = Typography;

const HomePage = () => {
  const [stats, setStats] = useState({
    cve: 0,
    technique: 0,
    lab: 0,
    defense: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/statistics');
      if (response.data.success) {
        setStats(response.data.data);
      }
    } catch (error) {
      console.error('获取统计失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <Title level={1}>AI 安全知识图谱平台</Title>
        <Paragraph style={{ fontSize: '18px', color: '#666' }}>
          基于知识图谱和LLM的下一代安全学习助手
        </Paragraph>
        <Link to="/graph">
          <Button type="primary" size="large" icon={<ArrowRightOutlined />}>
            开始探索
          </Button>
        </Link>
      </div>

      <Row gutter={[24, 24]}>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="CVE漏洞"
              value={stats.cve}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="攻击技术"
              value={stats.technique}
              prefix={<SafetyCertificateOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="靶场资源"
              value={stats.lab}
              prefix={<ExperimentOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable>
            <Statistic
              title="防御知识"
              value={stats.defense}
              prefix={<ReadOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <div style={{ marginTop: 48 }}>
        <Title level={3}>核心功能</Title>
        <Row gutter={[24, 24]}>
          <Col span={8}>
            <Card title="知识图谱可视化" bordered={false}>
              <Paragraph>
                直观展示漏洞、攻击技术、防御措施之间的复杂关系，帮助您建立完整的安全知识体系。
              </Paragraph>
              <Link to="/graph">查看图谱</Link>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="智能问答助手" bordered={false}>
              <Paragraph>
                集成大语言模型，基于知识图谱上下文回答您的安全问题，提供准确、专业的解答。
              </Paragraph>
              <Link to="/chat">开始提问</Link>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="靶场推荐" bordered={false}>
              <Paragraph>
                根据您的学习进度和感兴趣的技术点，智能推荐合适的靶场练习，理论结合实践。
              </Paragraph>
              <Link to="/labs">查找靶场</Link>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default HomePage;
