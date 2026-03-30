import React, { useEffect, useState } from 'react'
import {
  Table, Button, Space, Tag, Modal, Form, Input, InputNumber,
  message, Typography, Card, Row, Col, Statistic, Progress
} from 'antd'
import { PlusOutlined, EditOutlined, BarChartOutlined } from '@ant-design/icons'
import { enterpriseApi } from '../services/api'

const { Title } = Typography

const GRADE_COLOR = { S: 'gold', A: 'green', B: 'blue', C: 'orange', D: 'red' }
const getGrade = (s) => s >= 800 ? 'S' : s >= 650 ? 'A' : s >= 500 ? 'B' : s >= 350 ? 'C' : 'D'

export default function EnterprisePage() {
  const [list, setList] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [createModal, setCreateModal] = useState(false)
  const [scoreModal, setScoreModal] = useState(false)
  const [selectedEnt, setSelectedEnt] = useState(null)
  const [scoreData, setScoreData] = useState(null)
  const [form] = Form.useForm()
  const [scoreForm] = Form.useForm()

  const fetchList = async (p = page) => {
    setLoading(true)
    try {
      const res = await enterpriseApi.list({ page: p, page_size: 20 })
      setList(res.items)
      setTotal(res.total)
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchList() }, [])

  const openScoreModal = async (record) => {
    setSelectedEnt(record)
    const score = await enterpriseApi.getScore(record.id)
    setScoreData(score)
    scoreForm.setFieldsValue({
      operation_score: score.operation_score,
      innovation_score: score.innovation_score,
      credit_score: score.credit_score,
      growth_score: score.growth_score,
    })
    setScoreModal(true)
  }

  const handleCreate = async (values) => {
    try {
      await enterpriseApi.create(values)
      message.success('企业创建成功')
      setCreateModal(false)
      form.resetFields()
      fetchList()
    } catch (e) { message.error(e?.detail || '创建失败') }
  }

  const handleScoreUpdate = async (values) => {
    try {
      const res = await enterpriseApi.updateScore(selectedEnt.id, values)
      message.success(`评分更新成功，综合评分：${res.total_score}分`)
      setScoreModal(false)
      fetchList()
    } catch (e) { message.error(e?.detail || '更新失败') }
  }

  const columns = [
    { title: '企业名称', dataIndex: 'name', width: 200 },
    { title: '行业', dataIndex: 'industry', width: 100, render: v => v || '-' },
    { title: '省份', dataIndex: 'province', width: 80, render: v => v || '-' },
    { title: '员工数', dataIndex: 'employee_count', width: 80, render: v => v ? `${v}人` : '-' },
    {
      title: '综合评分', dataIndex: 'total_score', width: 120,
      sorter: (a, b) => a.total_score - b.total_score,
      render: (s) => {
        const grade = getGrade(s)
        return <Space>
          <strong style={{ color: '#1677ff' }}>{s}</strong>
          <Tag color={GRADE_COLOR[grade]}>{grade}级</Tag>
        </Space>
      }
    },
    {
      title: '状态', dataIndex: 'status', width: 80,
      render: s => s === 1 ? <Tag color="green">正常</Tag> : s === 2 ? <Tag color="orange">待审核</Tag> : <Tag color="red">禁用</Tag>
    },
    {
      title: '操作', width: 140, render: (_, record) => (
        <Space>
          <Button size="small" icon={<EditOutlined />} onClick={() => openScoreModal(record)}>评分</Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>企业管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModal(true)}>
          新增企业
        </Button>
      </div>

      <Card bordered={false} style={{ borderRadius: 8 }}>
        <Table
          rowKey="id"
          loading={loading}
          dataSource={list}
          columns={columns}
          pagination={{ total, pageSize: 20, current: page,
            onChange: p => { setPage(p); fetchList(p) } }}
          size="middle"
        />
      </Card>

      {/* Create Modal */}
      <Modal title="新增企业" open={createModal} onCancel={() => { setCreateModal(false); form.resetFields() }}
        footer={null} width={600}>
        <Form form={form} layout="vertical" onFinish={handleCreate} style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="企业名称" rules={[{ required: true }]}>
                <Input placeholder="请输入企业全称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="unified_code" label="统一社会信用代码">
                <Input placeholder="18位统一信用代码" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="industry" label="所属行业">
                <Input placeholder="如：新能源、智能制造" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="province" label="注册省份">
                <Input placeholder="如：广东省" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="city" label="注册城市">
                <Input placeholder="如：深圳市" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="employee_count" label="员工数量">
                <InputNumber min={1} style={{ width: '100%' }} placeholder="员工人数" />
              </Form.Item>
            </Col>
            <Col span={24}>
              <Form.Item name="description" label="企业简介">
                <Input.TextArea rows={3} placeholder="企业核心业务简介" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => { setCreateModal(false); form.resetFields() }}>取消</Button>
              <Button type="primary" htmlType="submit">确认创建</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Score Modal */}
      <Modal title={`企业评分 - ${selectedEnt?.name}`} open={scoreModal}
        onCancel={() => setScoreModal(false)} footer={null} width={600}>
        {scoreData && (
          <Card size="small" style={{ marginBottom: 16, background: '#f6f8ff' }}>
            <Row gutter={16}>
              <Col span={6}><Statistic title="综合评分" value={scoreData.total_score} suffix="分"
                valueStyle={{ color: '#1677ff' }} /></Col>
              <Col span={6}><Statistic title="经营维度" value={scoreData.operation_score} /></Col>
              <Col span={6}><Statistic title="创新维度" value={scoreData.innovation_score} /></Col>
              <Col span={6}><Statistic title="信用维度" value={scoreData.credit_score} /></Col>
            </Row>
          </Card>
        )}
        <Form form={scoreForm} layout="vertical" onFinish={handleScoreUpdate}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="operation_score" label="经营维度评分（0-400）">
                <InputNumber min={0} max={400} step={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="innovation_score" label="创新维度评分（0-300）">
                <InputNumber min={0} max={300} step={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="credit_score" label="信用维度评分（0-200）">
                <InputNumber min={0} max={200} step={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="growth_score" label="发展维度评分（0-100）">
                <InputNumber min={0} max={100} step={5} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => setScoreModal(false)}>取消</Button>
              <Button type="primary" htmlType="submit">更新评分</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
