import React, { useEffect, useState } from 'react';
import { 
  Card, 
  List, 
  Tag, 
  Space, 
  Typography, 
  Button,
  Select,
  Spin,
  message,
  Divider 
} from 'antd';
import { 
  ExperimentOutlined,
  LinkOutlined,
  CheckCircleOutlined,
  DollarOutlined,
  FireOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const LabsPage = () => {
  const [loading, setLoading] = useState(false);
  const [labs, setLabs] = useState([]);
  const [filterTechnique, setFilterTechnique] = useState(null);

  useEffect(() => {
    loadLabs();
  }, [filterTechnique]);

  const loadLabs = async () => {
    setLoading(true);
    try {
      const url = filterTechnique 
        ? `/api/labs?technique=${encodeURIComponent(filterTechnique)}`
        : '/api/labs';
      
      const response = await axios.get(url);
      
      if (response.data.success) {
        setLabs(response.data.data);
      }
    } catch (error) {
      message.error('加载靶场失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (difficulty) => {
    const colors = {
      '初级': 'green',
      '中级': 'orange',
      '高级': 'red',
      '初级到中级': 'blue',
      '初级到高级': 'purple',
      '初级到专家': 'magenta',
    };
    return colors[difficulty] || 'default';
  };

  const getDifficultyIcon = (difficulty) => {
    if (difficulty?.includes('高级') || difficulty?.includes('专家')) {
      return <FireOutlined />;
    }
    return null;
  };

  return (
    <div>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={2}>
              <ExperimentOutlined /> 实践靶场
            </Title>
            <Paragraph>
              精选的安全学习靶场，从初级到高级，涵盖Web安全、系统渗透、网络安全等多个领域。
              通过实际操作加深对安全知识的理解。
            </Paragraph>
          </div>

          <Space>
            <Text>筛选技术:</Text>
            <Select
              style={{ width: 200 }}
              placeholder="选择技术"
              allowClear
              onChange={setFilterTechnique}
              value={filterTechnique}
            >
              <Option value="SQL注入">SQL注入</Option>
              <Option value="XSS">XSS</Option>
              <Option value="CSRF">CSRF</Option>
              <Option value="命令注入">命令注入</Option>
              <Option value="文件包含">文件包含</Option>
            </Select>
            
            <Button type="primary" onClick={loadLabs} loading={loading}>
              刷新
            </Button>
          </Space>
        </Space>
      </Card>

      <Card style={{ marginTop: 16 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Spin size="large" tip="正在加载靶场..." />
          </div>
        ) : (
          <List
            itemLayout="vertical"
            size="large"
            pagination={{
              pageSize: 5,
              showSizeChanger: false,
              showTotal: (total) => `共 ${total} 个靶场`,
            }}
            dataSource={labs}
            renderItem={(lab) => (
              <List.Item
                key={lab.name}
                className="lab-card"
                actions={[
                  <Button 
                    type="primary"
                    icon={<LinkOutlined />}
                    onClick={() => window.open(lab.url, '_blank')}
                  >
                    访问靶场
                  </Button>,
                  lab.free ? (
                    <Tag icon={<CheckCircleOutlined />} color="success">
                      免费
                    </Tag>
                  ) : (
                    <Tag icon={<DollarOutlined />} color="warning">
                      付费
                    </Tag>
                  ),
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <ExperimentOutlined 
                      style={{ fontSize: '48px', color: '#1890ff' }} 
                    />
                  }
                  title={
                    <Space>
                      <Text strong style={{ fontSize: '18px' }}>
                        {lab.name}
                      </Text>
                      {lab.difficulty && (
                        <Tag 
                          color={getDifficultyColor(lab.difficulty)}
                          icon={getDifficultyIcon(lab.difficulty)}
                        >
                          {lab.difficulty}
                        </Tag>
                      )}
                    </Space>
                  }
                  description={
                    <div>
                      <Paragraph>
                        {lab.description}
                      </Paragraph>
                      
                      {lab.category && (
                        <div style={{ marginBottom: 8 }}>
                          <Tag color="blue">{lab.category}</Tag>
                        </div>
                      )}
                      
                      {lab.topics && lab.topics.length > 0 && (
                        <>
                          <Divider style={{ margin: '12px 0' }} />
                          <div>
                            <Text strong>涵盖主题: </Text>
                            <Space wrap>
                              {lab.topics.map((topic, idx) => (
                                <Tag key={idx} color="cyan">
                                  {topic}
                                </Tag>
                              ))}
                            </Space>
                          </div>
                        </>
                      )}
                      
                      <Divider style={{ margin: '12px 0' }} />
                      
                      <Space>
                        <Text type="secondary">
                          <LinkOutlined /> {lab.url}
                        </Text>
                      </Space>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      <Card style={{ marginTop: 16 }} title="💡 学习建议">
        <Space direction="vertical" size="middle">
          <div>
            <Text strong>1. 从基础开始</Text>
            <Paragraph>
              如果是初学者，推荐从DVWA、WebGoat等免费靶场开始，先掌握基础的Web漏洞。
            </Paragraph>
          </div>
          
          <div>
            <Text strong>2. 理论结合实践</Text>
            <Paragraph>
              学习每个漏洞原理后，立即在靶场中实践，加深理解。
            </Paragraph>
          </div>
          
          <div>
            <Text strong>3. 记录学习过程</Text>
            <Paragraph>
              建议记录每次练习的思路和方法，形成自己的知识库。
            </Paragraph>
          </div>
          
          <div>
            <Text strong>4. 循序渐进</Text>
            <Paragraph>
              掌握基础后，可以尝试HackTheBox、TryHackMe等更具挑战性的平台。
            </Paragraph>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default LabsPage;

