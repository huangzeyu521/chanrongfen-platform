import React, { useEffect, useState } from 'react'
import {
  Table, Button, Space, Tag, Modal, Form, Input, InputNumber,
  message, Typography, Card, Select, Descriptions, List
} from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { regionApi, enterpriseApi } from '../services/api'

const { Title } = Typography

export default function RegionPage() {
  const [list, setList] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [createModal, setCreateModal] = useState(false)
  const [matchModal, setMatchModal] = useState(false)
  const [matchRegion, setMatchRegion] = useState(null)
  const [matchResults, setMatchResults] = useState([])
  const [matchLoading, setMatchLoading] = useState(false)
  const [form] = Form.useForm()

  const fetchList = async (p = page) => {
    setLoading(true)
    try {
      const res = await regionApi.list({ page: p, page_size: 20 })
      setList(res.items); setTotal(res.total)
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchList() }, [])

  const handleCreate = async (values) => {
    try {
      if (values.industry_focus_arr) {
        values.industry_focus = JSON.stringify(values.industry_focus_arr)
        delete values.industry_focus_arr
      }
      await regionApi.create(values)
      message.success('区域需求创建成功')
      setCreateModal(false); form.resetFields(); fetchList()
    } catch (e) { message.error(e?.detail || '创建失败') }
  }

  const openMatchModal = async (record) => {
    setMatchRegion(record)
    setMatchResults([])
    setMatchModal(true)
    setMatchLoading(true)
    try {
      const res = await regionApi.topEnterprises(record.id, { top_n: 10, min_score: 30 })
      setMatchResults(res)
    } finally { setMatchLoading(false) }
  }

  const GRADE_COLOR = { S: 'gold', A: 'green', B: 'blue', C: 'orange', D: 'red' }
  const getMatchGrade = (s) => s >= 85 ? 'S' : s >= 70 ? 'A' : s >= 55 ? 'B' : s >= 40 ? 'C' : 'D'

  const columns = [
    { title: '区域/园区名称', dataIndex: 'name', width: 200 },
    { title: '省份', dataIndex: 'province', width: 80 },
    { title: '城市', dataIndex: 'city', width: 80, render: v => v || '-' },
    { title: '最低信用要求', dataIndex: 'credit_require', width: 120, render: v => `${v}分` },
    { title: '状态', dataIndex: 'status', width: 80,
      render: s => s === 1 ? <Tag color="green">有效</Tag> : <Tag color="red">过期</Tag> },
    { title: '操作', width: 120, render: (_, r) =>
      <Button size="small" icon={<SearchOutlined />} onClick={() => openMatchModal(r)}>匹配企业</Button> }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>区域产融需求</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModal(true)}>发布需求</Button>
      </div>
      <Card bordered={false} style={{ borderRadius: 8 }}>
        <Table rowKey="id" loading={loading} dataSource={list} columns={columns}
          pagination={{ total, pageSize: 20, current: page, onChange: p => { setPage(p); fetchList(p) } }} size="middle" />
      </Card>

      {/* Create Modal */}
      <Modal title="发布区域产融需求" open={createModal}
        onCancel={() => { setCreateModal(false); form.resetFields() }} footer={null} width={600}>
        <Form form={form} layout="vertical" onFinish={handleCreate} style={{ marginTop: 16 }}>
          <Form.Item name="name" label="区域/园区名称" rules={[{ required: true }]}>
            <Input placeholder="如：深圳新能源产业基地" />
          </Form.Item>
          <Form.Item name="province" label="省份" rules={[{ required: true }]}>
            <Input placeholder="如：广东省" />
          </Form.Item>
          <Form.Item name="city" label="城市">
            <Input placeholder="如：深圳市" />
          </Form.Item>
          <Form.Item name="industry_focus_arr" label="重点产业类型">
            <Select mode="tags" placeholder="输入产业类型后按Enter添加"
              options={['新能源','智能制造','生物医药','半导体','数字经济','现代农业'].map(v => ({ label: v, value: v }))} />
          </Form.Item>
          <Form.Item name="finance_scale" label="融资规模区间">
            <Input placeholder="如：1000万-1亿" />
          </Form.Item>
          <Form.Item name="credit_require" label="最低信用评分要求" initialValue={0}>
            <InputNumber min={0} max={200} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="contact_person" label="对接联系人">
            <Input />
          </Form.Item>
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => { setCreateModal(false); form.resetFields() }}>取消</Button>
              <Button type="primary" htmlType="submit">发布</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Match Modal */}
      <Modal title={`区域匹配企业 - ${matchRegion?.name}`} open={matchModal}
        onCancel={() => setMatchModal(false)} footer={null} width={700}>
        <List
          loading={matchLoading}
          dataSource={matchResults}
          renderItem={(item, idx) => (
            <List.Item>
              <List.Item.Meta
                avatar={<Tag color={GRADE_COLOR[getMatchGrade(item.match_score)]} style={{ fontSize: 16, padding: '4px 8px' }}>
                  #{idx + 1}
                </Tag>}
                title={<Space>
                  <span>{item.enterprise?.name}</span>
                  <Tag color={GRADE_COLOR[getMatchGrade(item.match_score)]}>
                    {getMatchGrade(item.match_score)}级匹配
                  </Tag>
                </Space>}
                description={`行业：${item.enterprise?.industry || '-'}  |  企业评分：${item.enterprise?.total_score}分`}
              />
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 22, fontWeight: 700, color: '#1677ff' }}>{item.match_score}</div>
                <div style={{ fontSize: 12, color: '#999' }}>匹配得分</div>
              </div>
            </List.Item>
          )}
        />
      </Modal>
    </div>
  )
}
