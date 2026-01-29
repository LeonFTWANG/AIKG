import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Input,
  Card,
  List,
  Tag,
  Space,
  Typography,
  Button,
  Empty,
  Spin,
  message
} from 'antd';
import {
  SearchOutlined,
  BugOutlined,
  ThunderboltOutlined,
  ExperimentOutlined,
  LinkOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Search } = Input;
const { Title, Paragraph, Text } = Typography;

const SearchPage = () => {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');

  useEffect(() => {
    const query = searchParams.get('q');
    if (query) {
      handleSearch(query);
    }
  }, [searchParams]);

  const handleSearch = async (value) => {
    if (!value.trim()) {
      message.warning('请输入搜索关键词');
      return;
    }

    setSearchQuery(value);
    setLoading(true);

    try {
      const response = await axios.post('/api/knowledge/search', {
        query: value,
        limit: 20
      });

      if (response.data.success) {
        setResults(response.data.data);
        message.success(`找到 ${response.data.count} 条结果`);
      }
    } catch (error) {
      message.error('搜索失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getTypeIcon = (type) => {
    const icons = {
      CVE: <BugOutlined style={{ color: '#ff4d4f' }} />,
      Technique: <ThunderboltOutlined style={{ color: '#fa8c16' }} />,
      Lab: <ExperimentOutlined style={{ color: '#1890ff' }} />,
      Defense: <LinkOutlined style={{ color: '#52c41a' }} />,
    };
    return icons[type] || <LinkOutlined />;
  };

  const getTypeColor = (type) => {
    const colors = {
      CVE: 'red',
      Technique: 'orange',
      Lab: 'blue',
      Defense: 'green',
      Tool: 'purple',
    };
    return colors[type] || 'default';
  };

  const getSeverityColor = (severity) => {
    const colors = {
      CRITICAL: 'red',
      HIGH: 'orange',
      MEDIUM: 'gold',
      LOW: 'green',
    };
    return colors[severity] || 'default';
  };

  const handleViewDetail = async (item) => {
    try {
      // 可以导航到详情页或打开模态框
      if (item.url) {
        window.open(item.url, '_blank');
      } else {
        message.info('请联系后台管理人员完善');
      }
    } catch (error) {
      message.error('操作失败');
    }
  };

  return (
    <div>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={2}>
              <SearchOutlined /> 搜索安全知识
            </Title>
            <Paragraph>
              搜索CVE漏洞、攻击技术、防御措施、靶场资源等安全知识点
            </Paragraph>
          </div>

          <Search
            placeholder="输入关键词搜索，如: SQL注入、XSS、CVE-2021-44228"
            size="large"
            enterButton="搜索"
            loading={loading}
            onSearch={handleSearch}
            allowClear
          />

          {searchQuery && (
            <Text type="secondary">
              搜索关键词: <Text strong>{searchQuery}</Text>
              {results.length > 0 && ` - 找到 ${results.length} 条结果`}
            </Text>
          )}
        </Space>
      </Card>

      <Card style={{ marginTop: 16 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" tip="正在搜索..." />
          </div>
        ) : results.length > 0 ? (
          <List
            itemLayout="vertical"
            size="large"
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 条结果`,
            }}
            dataSource={results}
            renderItem={(item) => (
              <List.Item
                key={item.name || item.id}
                className="knowledge-card"
                actions={[
                  <Button
                    type="link"
                    onClick={() => handleViewDetail(item)}
                  >
                    查看详情
                  </Button>
                ]}
              >
                <List.Item.Meta
                  avatar={getTypeIcon(item.type)}
                  title={
                    <Space>
                      <Text strong style={{ fontSize: '16px' }}>
                        {item.name}
                      </Text>
                      <Tag color={getTypeColor(item.type)}>
                        {item.type}
                      </Tag>
                      {item.severity && (
                        <Tag color={getSeverityColor(item.severity)}>
                          {item.severity}
                        </Tag>
                      )}
                    </Space>
                  }
                  description={
                    <div>
                      <Paragraph ellipsis={{ rows: 3, expandable: true }}>
                        {item.description || '暂无描述'}
                      </Paragraph>

                      {item.tags && item.tags.length > 0 && (
                        <div className="tag-container">
                          {item.tags.map((tag, idx) => (
                            <Tag key={idx}>{tag}</Tag>
                          ))}
                        </div>
                      )}

                      {item.cvss_score && (
                        <div style={{ marginTop: 8 }}>
                          <Text type="secondary">
                            CVSS评分: <Text strong>{item.cvss_score}</Text>
                          </Text>
                        </div>
                      )}

                      {item.category && (
                        <div style={{ marginTop: 4 }}>
                          <Text type="secondary">
                            分类: {item.category}
                          </Text>
                        </div>
                      )}
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        ) : (
          <Empty
            description={
              searchQuery
                ? "未找到相关结果，请尝试其他关键词"
                : "请输入关键词开始搜索"
            }
          />
        )}
      </Card>
    </div>
  );
};

export default SearchPage;

