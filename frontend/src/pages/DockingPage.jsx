import React, { useEffect, useState } from 'react'
import {
  Table, Button, Space, Tag, Modal, Form, Input, Select,
  message, Typography, Card, Steps, Descriptions
} from 'antd'
import { PlusOutlined, EyeOutlined } from '@ant-design/icons'
import { dockingApi } from '../services/api'

const { Title } = Typography

const STATUS_CONFIG = {
  draft:     { color: 'default',  label: '草稿' },
  submitted: { color: 'processing', label: '已提交' },
  approved:  { color: 'cyan',    label: '已审核' },
  ongoing:   { color: 'blue',    label: '对接中' },
  completed: { color: 'success', label: '已完成' },
  cancelled: { color: 'error',   label: '已取消' },
}

const TYPE_CONFIG = {
  ENT_GOV: { color: 'blue',   label: '企业-政府' },
  ENT_FIN: { color: 'green',  label: '企业-金融' },
  EXP_GOV: { color: 'purple', label: '专家-政府' },
  MEM_ACT: { color: 'orange', label: '会员活动' },
}

const STATUS_STEPS = ['draft', 'submitted', 'approved', 'ongoing', 'completed']

export default function DockingPage() {
  const [list, setList] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [createModal, setCreateModal] = useState(false)
  const [detailModal, setDetailModal] = useState(false)
  const [statusModal, setStatusModal] = useState(false)
  const [selected, setSelected] = useState(null)
  const [filterStatus, setFilterStatus] = useState(null)
  const [form] = Form.useForm()
  const [statusForm] = Form.useForm()

  const fetchList = async (p = page, status = filterStatus) => {
    setLoading(true)
    try {
      const params = { page: p, page_size: 20 }
      if (status) params.status = status
      const res = await dockingApi.list(params)
      setList(res.items); setTotal(res.total)
    } finally { setLoading(false) }
  }

  useEffect(() => { fetchList() }, [])

  const handleCreate = async (values) => {
    try {
      await dockingApi.create(values)
      message.success('对接申请创建成功')
      setCreateModal(false); form.resetFields(); fetchList()
    } catch (e) { message.error(e?.detail || '创建失败') }
  }

  const handleStatusUpdate = async (values) => {
    try {
      await dockingApi.updateStatus(selected.id, values)
      message.success('状态更新成功')
      setStatusModal(false); fetchList()
    } catch (e) { message.error(e?.detail || '更新失败') }
  }

  const columns = [
    { title: '对接标题', dataIndex: 'title', ellipsis: true, width: 220 },
    { title: '类型', dataIndex: 'type', width: 110,
      render: t => <Tag color={TYPE_CONFIG[t]?.color}>{TYPE_CONFIG[t]?.label || t}</Tag> },
    { title: '匹配分', dataIndex: 'match_score', width: 80,
      render: s => s > 0 ? <span style={{ color: '#1677ff', fontWeight: 600 }}>{s}</span> : '-' },
    { title: '状态', dataIndex: 'status', width: 100,
      render: s => <Tag color={STATUS_CONFIG[s]?.color}>{STATUS_CONFIG[s]?.label}</Tag> },
    { title: '申请日期', dataIndex: 'apply_date', width: 100, render: v => v || '-' },
    { title: '完成日期', dataIndex: 'complete_date', width: 100, render: v => v || '-' },
    {
      title: '操作', width: 150, render: (_, r) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => { setSelected(r); setDetailModal(true) }}>详情</Button>
          <Button size="small" type="primary" ghost onClick={() => {
            setSelected(r)
            statusForm.setFieldsValue({ status: r.status })
            setStatusModal(true)
          }}>更新状态</Button>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>对接管理</Title>
        <Space>
          <Select placeholder="筛选状态" allowClear style={{ width: 120 }}
            onChange={s => { setFilterStatus(s); fetchList(1, s) }}
            options={Object.entries(STATUS_CONFIG).map(([k, v]) => ({ value: k, label: v.label }))} />
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModal(true)}>发起对接</Button>
        </Space>
      </div>

      <Card bordered={false} style={{ borderRadius: 8 }}>
        <Table rowKey="id" loading={loading} dataSource={list} columns={columns}
          pagination={{ total, pageSize: 20, current: page,
            onChange: p => { setPage(p); fetchList(p) } }} size="middle" />
      </Card>

      {/* Create Modal */}
      <Modal title="发起对接申请" open={createModal}
        onCancel={() => { setCreateModal(false); form.resetFields() }} footer={null} width={560}>
        <Form form={form} layout="vertical" onFinish={handleCreate} style={{ marginTop: 16 }}>
          <Form.Item name="type" label="对接类型" rules={[{ required: true }]}>
            <Select options={Object.entries(TYPE_CONFIG).map(([k, v]) => ({ value: k, label: v.label }))} />
          </Form.Item>
          <Form.Item name="title" label="对接标题" rules={[{ required: true }]}>
            <Input placeholder="简要描述本次对接目标" />
          </Form.Item>
          <Form.Item name="initiator_id" label="发起方ID" rules={[{ required: true }]}>
            <Input placeholder="企业/专家 ID" />
          </Form.Item>
          <Form.Item name="target_id" label="对接目标ID" rules={[{ required: true }]}>
            <Input placeholder="区域/金融机构 ID" />
          </Form.Item>
          <Form.Item name="match_score" label="匹配得分" initialValue={0}>
            <Input type="number" min={0} max={100} />
          </Form.Item>
          <Form.Item name="description" label="对接需求描述">
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => { setCreateModal(false); form.resetFields() }}>取消</Button>
              <Button type="primary" htmlType="submit">提交申请</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Detail Modal */}
      <Modal title="对接详情" open={detailModal} onCancel={() => setDetailModal(false)} footer={null} width={600}>
        {selected && <>
          <Steps size="small" current={STATUS_STEPS.indexOf(selected.status)} style={{ marginBottom: 24 }}
            items={STATUS_STEPS.map(s => ({ title: STATUS_CONFIG[s]?.label }))} />
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="对接标题" span={2}>{selected.title}</Descriptions.Item>
            <Descriptions.Item label="对接类型"><Tag color={TYPE_CONFIG[selected.type]?.color}>{TYPE_CONFIG[selected.type]?.label}</Tag></Descriptions.Item>
            <Descriptions.Item label="匹配得分">{selected.match_score}分</Descriptions.Item>
            <Descriptions.Item label="发起方ID">{selected.initiator_id}</Descriptions.Item>
            <Descriptions.Item label="目标方ID">{selected.target_id}</Descriptions.Item>
            <Descriptions.Item label="申请日期">{selected.apply_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="完成日期">{selected.complete_date || '-'}</Descriptions.Item>
            <Descriptions.Item label="需求描述" span={2}>{selected.description || '-'}</Descriptions.Item>
            <Descriptions.Item label="对接结果" span={2}>{selected.result || '-'}</Descriptions.Item>
            <Descriptions.Item label="备注" span={2}>{selected.remark || '-'}</Descriptions.Item>
          </Descriptions>
        </>}
      </Modal>

      {/* Status Update Modal */}
      <Modal title="更新对接状态" open={statusModal} onCancel={() => setStatusModal(false)} footer={null} width={400}>
        <Form form={statusForm} layout="vertical" onFinish={handleStatusUpdate} style={{ marginTop: 16 }}>
          <Form.Item name="status" label="新状态" rules={[{ required: true }]}>
            <Select options={Object.entries(STATUS_CONFIG).map(([k, v]) => ({ value: k, label: v.label }))} />
          </Form.Item>
          <Form.Item name="remark" label="审核备注">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item name="result" label="对接结果（完成时填写）">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => setStatusModal(false)}>取消</Button>
              <Button type="primary" htmlType="submit">确认更新</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
