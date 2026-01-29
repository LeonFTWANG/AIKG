import React, { useEffect, useRef, useState } from 'react';
import { Card, Space, Button, Select, InputNumber, Spin, message } from 'antd';
import { ReloadOutlined, ZoomInOutlined, ZoomOutOutlined } from '@ant-design/icons';
import { Network } from 'vis-network';
import axios from 'axios';

const { Option } = Select;

const GraphPage = () => {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [limit, setLimit] = useState(100);
  const [layout, setLayout] = useState('physics');

  useEffect(() => {
    loadGraph();
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
      }
    };
  }, []);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/graph/visualization?limit=${limit}`);
      
      if (response.data.success) {
        renderGraph(response.data.data);
        message.success('图谱加载成功');
      }
    } catch (error) {
      message.error('加载图谱失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const renderGraph = (data) => {
    if (!containerRef.current) return;

    // 清除旧图
    if (networkRef.current) {
      networkRef.current.destroy();
    }

    const { nodes, edges } = data;

    // 节点样式配置
    const nodeColors = {
      CVE: '#ff4d4f',
      Technique: '#fa8c16',
      Lab: '#1890ff',
      Defense: '#52c41a',
      Tool: '#722ed1',
      Unknown: '#8c8c8c',
    };

    // 处理节点
    const visNodes = nodes.map(node => ({
      id: node.id,
      label: node.label || node.properties?.name || 'Unknown',
      title: `${node.type}\n${node.properties?.description || ''}`.substring(0, 200),
      color: nodeColors[node.type] || nodeColors.Unknown,
      shape: 'dot',
      size: 20,
      font: { size: 14 }
    }));

    // 处理边
    const visEdges = edges.map((edge, idx) => ({
      id: `edge-${idx}`,
      from: edge.source,
      to: edge.target,
      label: edge.type,
      arrows: 'to',
      color: { color: '#999' },
      font: { size: 10, align: 'middle' }
    }));

    // 创建网络
    const graphData = {
      nodes: visNodes,
      edges: visEdges,
    };

    const options = {
      nodes: {
        shape: 'dot',
        font: {
          size: 14,
          color: '#333'
        },
        borderWidth: 2,
        shadow: true
      },
      edges: {
        width: 2,
        smooth: {
          type: 'continuous'
        },
        font: {
          size: 10,
          align: 'middle'
        }
      },
      physics: {
        enabled: layout === 'physics',
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.3,
          springLength: 200,
          springConstant: 0.04
        },
        stabilization: {
          iterations: 150
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true
      },
      layout: {
        improvedLayout: true,
      }
    };

    networkRef.current = new Network(containerRef.current, graphData, options);

    // 点击节点事件
    networkRef.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = nodes.find(n => n.id === nodeId);
        if (node) {
          message.info(`节点: ${node.label} (${node.type})`);
        }
      }
    });

    // 双击节点展开相关知识
    networkRef.current.on('doubleClick', async (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = nodes.find(n => n.id === nodeId);
        if (node && node.label) {
          try {
            const response = await axios.get(
              `/api/knowledge/${encodeURIComponent(node.label)}/related?depth=1`
            );
            if (response.data.success) {
              message.success(`找到 ${response.data.data.nodes.length} 个相关节点`);
              // 这里可以扩展图谱显示相关节点
            }
          } catch (error) {
            message.error('获取相关知识失败');
          }
        }
      }
    });
  };

  const handleZoomIn = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 1.2 });
    }
  };

  const handleZoomOut = () => {
    if (networkRef.current) {
      const scale = networkRef.current.getScale();
      networkRef.current.moveTo({ scale: scale * 0.8 });
    }
  };

  const handleReset = () => {
    if (networkRef.current) {
      networkRef.current.fit();
    }
  };

  return (
    <div>
      <Card className="graph-controls">
        <Space wrap>
          <span>节点数量:</span>
          <InputNumber
            min={10}
            max={500}
            value={limit}
            onChange={setLimit}
          />
          
          <span>布局:</span>
          <Select
            value={layout}
            onChange={setLayout}
            style={{ width: 120 }}
          >
            <Option value="physics">物理布局</Option>
            <Option value="hierarchical">层次布局</Option>
          </Select>
          
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={loadGraph}
            loading={loading}
          >
            加载图谱
          </Button>
          
          <Button icon={<ZoomInOutlined />} onClick={handleZoomIn}>
            放大
          </Button>
          
          <Button icon={<ZoomOutOutlined />} onClick={handleZoomOut}>
            缩小
          </Button>
          
          <Button onClick={handleReset}>
            重置视图
          </Button>
        </Space>
      </Card>

      <Card
        title="知识图谱可视化"
        extra={
          <Space>
            <span style={{ color: '#ff4d4f' }}>● CVE</span>
            <span style={{ color: '#fa8c16' }}>● 技术</span>
            <span style={{ color: '#1890ff' }}>● 靶场</span>
            <span style={{ color: '#52c41a' }}>● 防御</span>
            <span style={{ color: '#722ed1' }}>● 工具</span>
          </Space>
        }
      >
        {loading && (
          <div style={{ textAlign: 'center', padding: '100px' }}>
            <Spin size="large" tip="正在加载知识图谱..." />
          </div>
        )}
        
        <div
          ref={containerRef}
          style={{
            width: '100%',
            height: '70vh',
            border: '1px solid #d9d9d9',
            borderRadius: '4px'
          }}
        />
        
        <div style={{ marginTop: 16, color: '#8c8c8c' }}>
          💡 提示: 单击节点查看信息，双击节点展开相关知识，滚轮缩放，拖拽移动
        </div>
      </Card>
    </div>
  );
};

export default GraphPage;

