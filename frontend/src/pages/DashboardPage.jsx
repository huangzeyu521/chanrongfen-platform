import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Spin, Typography } from 'antd'
import { BankOutlined, UserOutlined, SwapOutlined, TrophyOutlined, RiseOutlined } from '@ant-design/icons'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { dashboardApi } from '../services/api'

const { Title } = Typography

const GRADE_COLOR = { S: 'gold', A: 'green', B: 'blue', C: 'orange', D: 'red' }

export default function DashboardPage() {
  const [overview, setOverview] = useState(null)
  const [distribution, setDistribution] = useState([])
  const [trends, setTrends] = useState([])
  const [topEnts, setTopEnts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      dashboardApi.overview(),
      dashboardApi.scoreDistribution(),
      dashboardApi.trends(),
      dashboardApi.topEnterprises()
    ]).then(([ov, dist, tr, top]) => {
      setOverview(ov)
      setDistribution(dist)
      setTrends(tr)
      setTopEnts(top)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>

  const topColumns = [
    { title: '排名', dataIndex: 'rank', width: 60, render: r => <Tag color={r <= 3 ? 'gold' : 'default'}>#{r}</Tag> },
    { title: '企业名称', dataIndex: 'name' },
    { title: '行业', dataIndex: 'industry', render: v => v || '-' },
    { title: '综合评分', dataIndex: 'total_score', render: s => <strong style={{ color: '#1677ff' }}>{s}分</strong> },
  ]

  return (
    <div>
      <Title level={4} style={{ marginBottom: 24 }}>数据看板</Title>

      {/* KPI Cards */}
      <Row gutter={[16, 16]}>
        {[
          { title: '会员企业', value: overview?.total_enterprises, icon: <BankOutlined />, color: '#1677ff' },
          { title: '专家资源', value: overview?.total_experts, icon: <UserOutlined />, color: '#52c41a' },
          { title: '对接申请', value: overview?.total_dockings, icon: <SwapOutlined />, color: '#fa8c16' },
          { title: '平均企业评分', value: overview?.avg_enterprise_score, suffix: '分', icon: <RiseOutlined />, color: '#722ed1' },
        ].map((item, i) => (
          <Col xs={24} sm={12} lg={6} key={i}>
            <Card bordered={false} style={{ borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Statistic title={item.title} value={item.value} suffix={item.suffix}
                  valueStyle={{ color: item.color, fontSize: 28 }} />
                <div style={{ fontSize: 36, color: item.color, opacity: 0.15 }}>{item.icon}</div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* Score Distribution */}
        <Col xs={24} lg={12}>
          <Card title="企业评分分布" bordered={false} style={{ borderRadius: 8 }}>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={distribution}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="range" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#1677ff" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Docking Trends */}
        <Col xs={24} lg={12}>
          <Card title="对接趋势（近12月）" bordered={false} style={{ borderRadius: 8 }}>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="total" stroke="#1677ff" name="申请数" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="completed" stroke="#52c41a" name="完成数" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Top Enterprises */}
        <Col xs={24}>
          <Card title="企业评分 TOP 10" bordered={false} style={{ borderRadius: 8 }}>
            <Table
              dataSource={topEnts}
              columns={topColumns}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
