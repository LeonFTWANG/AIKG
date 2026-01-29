import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Input,
  Button,
  Space,
  Typography,
  Tag,
  Divider,
  Empty,
  Spin,
  message,
  List,
  Layout,
  Menu,
  Avatar,
  Modal,
  Collapse,
  Alert
} from 'antd';
import {
  SendOutlined,
  RobotOutlined,
  UserOutlined,
  ClearOutlined,
  BulbOutlined,
  PlusOutlined,
  MessageOutlined,
  DeleteOutlined,
  SafetyCertificateOutlined,
  BugOutlined,
  WarningOutlined,
  MedicineBoxOutlined,
  AimOutlined,
  LinkOutlined
} from '@ant-design/icons';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { useAuth } from '../context/AuthContext';

const { TextArea } = Input;
const { Title, Paragraph, Text, Link } = Typography;
const { Sider, Content } = Layout;
const { Panel } = Collapse;

const StructuredResponse = ({ content }) => {
  let data = null;
  try {
    data = JSON.parse(content);
    // 简单的验证是否包含关键字段，区分JSON和普通文本
    if (!data.vulnerability_introduction && !data.vulnerability_principle) {
      data = null;
    }
  } catch (e) {
    data = null;
  }

  if (!data) {
    return (
      <div style={{ padding: '0 8px' }}>
        <ReactMarkdown>
          {content}
        </ReactMarkdown>
      </div>
    );
  }

  return (
    <Space direction="vertical" style={{ width: '100%', gap: '16px' }}>
      {/* 漏洞介绍 */}
      <Card
        size="small"
        title={<Space><SafetyCertificateOutlined style={{ color: '#1890ff' }} /> 漏洞介绍</Space>}
        headStyle={{ background: '#f0f5ff', borderBottom: '1px solid #d6e4ff' }}
        bodyStyle={{ padding: '12px' }}
      >
        <ReactMarkdown>{data.vulnerability_introduction}</ReactMarkdown>
      </Card>

      {/* 漏洞原理 */}
      <Card
        size="small"
        title={<Space><BugOutlined style={{ color: '#faad14' }} /> 漏洞原理</Space>}
        headStyle={{ background: '#fff7e6', borderBottom: '1px solid #ffd591' }}
        bodyStyle={{ padding: '12px' }}
      >
        <ReactMarkdown>{data.vulnerability_principle}</ReactMarkdown>
      </Card>

      {/* 经典案例 */}
      <Card
        size="small"
        title={<Space><WarningOutlined style={{ color: '#ff4d4f' }} /> 经典案例</Space>}
        headStyle={{ background: '#fff1f0', borderBottom: '1px solid #ffa39e' }}
        bodyStyle={{ padding: '12px' }}
      >
        <ReactMarkdown>{data.classic_cases}</ReactMarkdown>
      </Card>

      {/* 预防措施 */}
      <Card
        size="small"
        title={<Space><MedicineBoxOutlined style={{ color: '#52c41a' }} /> 预防措施</Space>}
        headStyle={{ background: '#f6ffed', borderBottom: '1px solid #b7eb8f' }}
        bodyStyle={{ padding: '12px' }}
      >
        <ReactMarkdown>{data.preventive_measures}</ReactMarkdown>
      </Card>

      {/* 实践靶场 */}
      <Card
        size="small"
        title={<Space><AimOutlined style={{ color: '#722ed1' }} /> 实践靶场</Space>}
        headStyle={{ background: '#f9f0ff', borderBottom: '1px solid #d3adf7' }}
        bodyStyle={{ padding: '12px' }}
      >
        <ReactMarkdown>{data.practice_range}</ReactMarkdown>
      </Card>

      {/* 相关链接 */}
      {data.relevant_links && data.relevant_links.length > 0 && (
        <Alert
          message={
            <Space>
              <LinkOutlined />
              <Text strong>相关资源:</Text>
              {data.relevant_links.map((link, idx) => (
                <Link key={idx} href={link.url} target="_blank" rel="noopener noreferrer">
                  {link.name}
                </Link>
              ))}
            </Space>
          }
          type="info"
          showIcon={false}
          style={{ padding: '8px 16px' }}
        />
      )}
    </Space>
  );
};

const ChatPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Load conversation ID from session storage on mount
  useEffect(() => {
    const savedId = sessionStorage.getItem('currentConversationId');
    if (savedId) {
      setCurrentConversationId(savedId);
    }
  }, []);

  // Save conversation ID to session storage when it changes
  useEffect(() => {
    if (currentConversationId) {
      sessionStorage.setItem('currentConversationId', currentConversationId);
    } else {
      sessionStorage.removeItem('currentConversationId');
    }
  }, [currentConversationId]);

  // Fetch conversations list
  useEffect(() => {
    if (user) {
      fetchConversations();
    }
  }, [user]);

  // Fetch messages when conversation changes
  useEffect(() => {
    if (user && currentConversationId) {
      fetchMessages(currentConversationId);
    } else {
      setMessages([]);
    }
  }, [user, currentConversationId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversations = async () => {
    setListLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/chat/conversations');
      if (response.data.success) {
        setConversations(response.data.data);
      }
    } catch (error) {
      console.error('获取对话列表失败:', error);
    } finally {
      setListLoading(false);
    }
  };

  const fetchMessages = async (conversationId) => {
    setLoading(true);
    try {
      const response = await axios.get(`http://localhost:8000/api/chat/conversations/${conversationId}/messages`);
      if (response.data.success) {
        const history = response.data.data.map(item => ([
          { role: 'user', content: item.question, timestamp: item.timestamp },
          { role: 'assistant', content: item.answer, timestamp: item.timestamp, relatedKnowledge: item.related_knowledge }
        ])).flat();
        setMessages(history);
      }
    } catch (error) {
      console.error('获取消息失败:', error);
      message.error('获取消息记录失败');
    } finally {
      setLoading(false);
    }
  };

  const createConversation = async (title = "New Chat") => {
    try {
      const response = await axios.post('http://localhost:8000/api/chat/conversations', { title });
      if (response.data.success) {
        const newConv = response.data.data;
        setConversations([newConv, ...conversations]);
        setCurrentConversationId(newConv.id);
        return newConv.id;
      }
    } catch (error) {
      console.error('创建对话失败:', error);
      message.error('创建新对话失败');
      return null;
    }
  };

  const handleNewChat = () => {
    setCurrentConversationId(null);
    setMessages([]);
    setInputValue('');
  };

  const handleSend = async () => {
    if (!inputValue.trim()) {
      message.warning('请输入问题');
      return;
    }

    if (!user) {
      message.warning('请先登录');
      return;
    }

    let conversationId = currentConversationId;
    if (!conversationId) {
      // Create new conversation first
      const title = inputValue.slice(0, 20) + (inputValue.length > 20 ? '...' : '');
      conversationId = await createConversation(title);
      if (!conversationId) return;
    }

    const userMessage = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/llm/query', {
        question: userMessage.content,
        context_depth: 2,
        conversation_id: conversationId
      });

      if (response.data.success) {
        const assistantMessage = {
          role: 'assistant',
          content: response.data.data.answer,
          relatedKnowledge: response.data.data.related_knowledge,
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, assistantMessage]);
        // Refresh list to update timestamp/order if needed
        fetchConversations();
      }
    } catch (error) {
      message.error('查询失败: ' + error.message);
      const errorMessage = {
        role: 'assistant',
        content: '抱歉，处理您的问题时出现了错误。请稍后再试。',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConversation = async (conversationId, e) => {
    // 阻止事件冒泡，避免触发选中对话
    e.stopPropagation();

    // 验证conversationId有效性
    if (!conversationId || conversationId === 'null' || conversationId === 'undefined') {
      message.error('无效的对话ID，无法删除');
      console.error('尝试删除无效的对话ID:', conversationId);
      return;
    }

    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个对话吗？删除后无法恢复。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await axios.delete(`http://localhost:8000/api/chat/conversations/${conversationId}`);
          if (response.data.success) {
            message.success('对话已删除');

            // 如果删除的是当前对话，清空消息并重置状态
            if (conversationId === currentConversationId) {
              setCurrentConversationId(null);
              setMessages([]);
            }

            // 刷新对话列表
            fetchConversations();
          }
        } catch (error) {
          console.error('删除对话失败:', error);
          message.error('删除对话失败: ' + (error.response?.data?.detail || error.message));
        }
      }
    });
  };

  const handleQuickQuestion = (question) => {
    setInputValue(question);
  };

  const quickQuestions = [
    "什么是SQL注入攻击？",
    "如何防御XSS攻击？",
    "CSRF攻击的原理是什么？",
    "推荐一些Web安全学习靶场",
    "什么是OWASP Top 10？",
  ];

  return (
    <Layout style={{ height: 'calc(100vh - 64px)', background: '#fff' }}>
      <Sider width={250} theme="light" style={{ borderRight: '1px solid #f0f0f0' }}>
        <div style={{ padding: '16px' }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            block
            onClick={handleNewChat}
          >
            新对话
          </Button>
        </div>
        <Divider style={{ margin: '0' }} />
        <div style={{ overflowY: 'auto', height: 'calc(100% - 70px)' }}>
          <List
            loading={listLoading}
            dataSource={conversations.filter(item => item && item.id)}
            renderItem={item => (
              <List.Item
                className="conversation-item"
                style={{
                  padding: '12px 16px',
                  cursor: 'pointer',
                  background: currentConversationId === item.id ? '#e6f7ff' : 'transparent',
                  borderRight: currentConversationId === item.id ? '3px solid #1890ff' : 'none',
                  position: 'relative'
                }}
                onClick={() => setCurrentConversationId(item.id)}
              >
                <div style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <Text ellipsis style={{ width: '100%', display: 'block' }}>
                      <MessageOutlined style={{ marginRight: 8 }} />
                      {item.title}
                    </Text>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {new Date(item.updated_at || item.created_at).toLocaleDateString()}
                    </Text>
                  </div>
                  <Button
                    type="text"
                    danger
                    size="small"
                    icon={<DeleteOutlined />}
                    onClick={(e) => handleDeleteConversation(item.id, e)}
                    style={{ marginLeft: 8 }}
                    className="delete-btn"
                  />
                </div>
              </List.Item>
            )}
          />
        </div>
      </Sider>

      <Content style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
        {!currentConversationId && messages.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Space direction="vertical" align="center" size="large">
              <RobotOutlined style={{ fontSize: '64px', color: '#1890ff' }} />
              <Title level={3}>AI 安全助手</Title>
              <Paragraph type="secondary">
                开始一个新的对话，探索 AI 安全知识图谱
              </Paragraph>
              <div>
                <Text strong><BulbOutlined /> 试着问问:</Text>
                <div style={{ marginTop: 16, maxWidth: 600 }}>
                  <Space wrap>
                    {quickQuestions.map((q, idx) => (
                      <Tag
                        key={idx}
                        style={{ cursor: 'pointer', padding: '4px 10px', marginBottom: 8 }}
                        onClick={() => handleQuickQuestion(q)}
                      >
                        {q}
                      </Tag>
                    ))}
                  </Space>
                </div>
              </div>
            </Space>
          </div>
        ) : (
          <div className="chat-messages" style={{ flex: 1, overflowY: 'auto', marginBottom: 24, paddingRight: 16 }}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`message message-${msg.role}`}
                style={{ marginBottom: 24 }}
              >
                <Space align="start" style={{ width: '100%', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
                  <Avatar
                    icon={msg.role === 'user' ? <UserOutlined /> : <RobotOutlined />}
                    style={{ backgroundColor: msg.role === 'user' ? '#87d068' : '#1890ff' }}
                  />

                  <div style={{
                    maxWidth: '80%',
                    textAlign: msg.role === 'user' ? 'right' : 'left'
                  }}>
                    <div style={{
                      display: 'inline-block',
                      padding: '12px 16px',
                      background: msg.role === 'user' ? '#95de64' : '#f0f2f5',
                      borderRadius: '8px',
                      textAlign: 'left'
                    }}>
                      <div style={{
                        width: '100%',
                        overflow: 'hidden'
                      }}>
                        <StructuredResponse content={msg.content} />
                      </div>
                    </div>

                    {msg.relatedKnowledge && msg.relatedKnowledge.length > 0 && (
                      <Card size="small" style={{ marginTop: 8, textAlign: 'left' }}>
                        <Text strong>📚 相关知识点:</Text>
                        <div style={{ marginTop: 8 }}>
                          {msg.relatedKnowledge.slice(0, 3).map((item, i) => (
                            <Tag
                              key={i}
                              color="blue"
                              style={{ marginBottom: 4, cursor: 'pointer' }}
                              onClick={() => navigate(`/search?q=${encodeURIComponent(item.name)}`)}
                            >
                              {item.name}
                            </Tag>
                          ))}
                        </div>
                      </Card>
                    )}
                  </div>
                </Space>
              </div>
            ))}

            {loading && (
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <Spin tip="AI正在思考..." />
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}

        <div className="chat-input-container">
          <Space.Compact style={{ width: '100%' }}>
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onPressEnter={(e) => {
                if (e.ctrlKey) {
                  handleSend();
                }
              }}
              placeholder="输入你的问题... (Ctrl+Enter发送)"
              autoSize={{ minRows: 2, maxRows: 6 }}
              disabled={loading}
              style={{ flex: 1 }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={loading}
              style={{ height: 'auto' }}
            >
              发送
            </Button>
          </Space.Compact>
        </div>
      </Content>
    </Layout>
  );
};

export default ChatPage;
