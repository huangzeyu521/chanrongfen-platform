import React, { useEffect, useState } from 'react'
import {
  Table, Button, Space, Tag, Modal, Form, Input, InputNumber,
  message, Typography, Card, Row, Col, Statistic
} from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { expertApi } from '../services/api'

const { Title } = Typography

const GRADE_LABELS = { S: { color: 'gold', label: 'S级 市长级' }, A: { color: 'green', label: 'A级 副市长级' },
  B: { color: 'blue', label: 'B级 副区长级' }, C: { color: 'orange', label: 'C级 局长级' }, D: { color: 'default', label: 'D级' } }

export default function ExpertPage() {
  const [list, setList] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [createModal, setCreateModal] = useState(false)
  const [scoreModal, setScoreModal] = useState(false)
  const [selected, setSelected] = useState(null)
  const [form] = Form.useForm()
  const [scoreForm] = Form.useForm()

  const fetchList = async (p = page) => {
    setLoading(true)
    try {
      const res = await expertApi.list({ page: p, page_size: 20 })
      setList(res.items); setTotal(res.total)
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchList() }, [])

  const handleCreate = async (values) => {
    try {
      await expertApi.create(values)
      message.success('专家创建成功')
      setCreateModal(false); form.resetFields(); fetchList()
    } catch (e) { message.error(e?.detail || '创建失败') }
  }

  const openScoreModal = (record) => {
    setSelected(record)
    scoreForm.setFieldsValue({
      capability_score: record.capability_score,
      adaptability_score: record.adaptability_score,
      willingness_score: record.willingness_score,
    })
    setScoreModal(true)
  }

  const handleScoreUpdate = async (values) => {
    try {
      const res = await expertApi.updateScore(selected.id, values)
      message.success(`评分更新成功：${res.total_score}分 ${res.grade}级`)
      setScoreModal(false); fetchList()
    } catch (e) { message.error(e?.detail || '更新失败') }
  }

  const columns = [
    { title: '专家姓名', dataIndex: 'name', width: 100 },
    { title: '职称', dataIndex: 'title', width: 200, render: v => v || '-', ellipsis: true },
    { title: '专业领域', dataIndex: 'domain', width: 120, render: v => v || '-' },
    { title: '所属机构', dataIndex: 'institution', width: 150, render: v => v || '-', ellipsis: true },
    { title: '综合评分', dataIndex: 'total_score', width: 100, sorter: (a, b) => a.total_score - b.total_score,
      render: s => <strong style={{ color: '#1677ff' }}>{s}分</strong> },
    { title: '对接规格', dataIndex: 'grade', width: 140,
      render: g => g ? <Tag color={GRADE_LABELS[g]?.color}>{GRADE_LABELS[g]?.label || g}</Tag> : <Tag>未评分</Tag> },
    { title: '操作', width: 100, render: (_, r) =>
      <Button size="small" icon={<EditOutlined />} onClick={() => openScoreModal(r)}>评分</Button> }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>专家管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModal(true)}>新增专家</Button>
      </div>
      <Card bordered={false} style={{ borderRadius: 8 }}>
        <Table rowKey="id" loading={loading} dataSource={list} columns={columns}
          pagination={{ total, pageSize: 20, current: page, onChange: p => { setPage(p); fetchList(p) } }} size="middle" />
      </Card>

      <Modal title="新增专家" open={createModal} onCancel={() => { setCreateModal(false); form.resetFields() }} footer={null} width={560}>
        <Form form={form} layout="vertical" onFinish={handleCreate} style={{ marginTop: 16 }}>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="name" label="专家姓名" rules={[{ required: true }]}><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="domain" label="专业领域"><Input placeholder="如：新能源、智能制造" /></Form.Item></Col>
            <Col span={24}><Form.Item name="title" label="职称/头衔"><Input placeholder="如：清华大学教授、中科院院士" /></Form.Item></Col>
            <Col span={24}><Form.Item name="institution" label="所属机构"><Input /></Form.Item></Col>
            <Col span={24}><Form.Item name="bio" label="简介"><Input.TextArea rows={3} /></Form.Item></Col>
          </Row>
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => { setCreateModal(false); form.resetFields() }}>取消</Button>
              <Button type="primary" htmlType="submit">确认</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal title={`专家三维评分 - ${selected?.name}`} open={scoreModal}
        onCancel={() => setScoreModal(false)} footer={null} width={520}>
        {selected && (
          <Card size="small" style={{ marginBottom: 16, background: '#f6f8ff' }}>
            <Row gutter={16}>
              <Col span={6}><Statistic title="综合评分" value={selected.total_score} suffix="分" valueStyle={{ color: '#1677ff' }} /></Col>
              <Col span={6}><Statistic title="专业能力" value={selected.capability_score} /></Col>
              <Col span={6}><Statistic title="适配度" value={selected.adaptability_score} /></Col>
              <Col span={6}><Statistic title="意愿度" value={selected.willingness_score} /></Col>
            </Row>
          </Card>
        )}
        <Form form={scoreForm} layout="vertical" onFinish={handleScoreUpdate}>
          <Form.Item name="capability_score" label="专业能力与影响力（0-500，权重50%）">
            <InputNumber min={0} max={500} step={10} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="adaptability_score" label="场景适配度（0-300，权重30%）">
            <InputNumber min={0} max={300} step={10} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="willingness_score" label="参与意愿度（0-200，权重20%）">
            <InputNumber min={0} max={200} step={10} style={{ width: '100%' }} />
          </Form.Item>
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
