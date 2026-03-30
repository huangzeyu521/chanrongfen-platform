import React, { useEffect, useState } from 'react'
import {
  Table, Button, Space, Tag, Modal, Form, Input, InputNumber,
  Select, message, Typography, Card, Statistic, Row, Col, List, Avatar, Progress
} from 'antd'
import { TrophyOutlined, PlusOutlined } from '@ant-design/icons'
import { memberApi, enterpriseApi } from '../services/api'

const { Title } = Typography

const GRADE_COLOR = { S: '#faad14', A: '#52c41a', B: '#1677ff', C: '#fa8c16' }
const GRADE_LABEL = { S: '卓越贡献', A: '积极贡献', B: '标准贡献', C: '待提升' }

const ACTION_OPTIONS = [
  { value: 'fee_paid', label: '会费缴纳（+20分）' },
  { value: 'recommend_member', label: '推荐新会员（+50分）' },
  { value: 'recommend_project', label: '推荐优质项目（+30分）' },
  { value: 'join_activity', label: '参与协会活动（+5分）' },
  { value: 'organize_activity', label: '组织专题活动（+20分）' },
  { value: 'gov_resource', label: '对接政府资源（+30分）' },
  { value: 'expert_service', label: '提供专家服务（+20分）' },
]

const ACTION_SCORES = {
  fee_paid: 20, recommend_member: 50, recommend_project: 30,
  join_activity: 5, organize_activity: 20, gov_resource: 30, expert_service: 20
}

export default function MemberPage() {
  const [leaderboard, setLeaderboard] = useState([])
  const [lbLoading, setLbLoading] = useState(false)
  const [recordModal, setRecordModal] = useState(false)
  const [queryModal, setQueryModal] = useState(false)
  const [queryResult, setQueryResult] = useState(null)
  const [queryLoading, setQueryLoading] = useState(false)
  const [queryId, setQueryId] = useState('')
  const [form] = Form.useForm()

  const fetchLeaderboard = async () => {
    setLbLoading(true)
    try {
      const res = await memberApi.leaderboard({ top_n: 20 })
      setLeaderboard(res)
    } finally { setLbLoading(false) }
  }

  useEffect(() => { fetchLeaderboard() }, [])

  const handleRecord = async (values) => {
    values.score_earned = ACTION_SCORES[values.action_type] || values.score_earned || 0
    try {
      await memberApi.recordContribution(values)
      message.success('贡献记录已保存')
      setRecordModal(false); form.resetFields(); fetchLeaderboard()
    } catch (e) { message.error(e?.detail || '保存失败') }
  }

  const handleQuery = async () => {
    if (!queryId.trim()) return message.warning('请输入企业ID')
    setQueryLoading(true)
    try {
      const res = await memberApi.getContribution(queryId.trim())
      setQueryResult(res)
    } catch (e) {
      message.error(e?.detail || '查询失败，请检查企业ID')
    } finally { setQueryLoading(false) }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>会员贡献管理</Title>
        <Space>
          <Button onClick={() => setQueryModal(true)}>查询贡献分</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setRecordModal(true)}>记录贡献行为</Button>
        </Space>
      </div>

      {/* Leaderboard */}
      <Card title={<Space><TrophyOutlined style={{ color: '#faad14' }} />贡献分排行榜 TOP 20</Space>}
        bordered={false} style={{ borderRadius: 8 }} loading={lbLoading}>
        <List
          dataSource={leaderboard}
          renderItem={(item, idx) => (
            <List.Item>
              <List.Item.Meta
                avatar={
                  <Avatar style={{
                    background: idx === 0 ? '#faad14' : idx === 1 ? '#bfbfbf' : idx === 2 ? '#d48806' : '#f0f0f0',
                    color: idx < 3 ? '#fff' : '#666', fontWeight: 700
                  }}>{idx + 1}</Avatar>
                }
                title={<Space>
                  <span style={{ fontWeight: 600 }}>{item.enterprise_name}</span>
                  <Tag color={GRADE_COLOR[item.grade]}>{GRADE_LABEL[item.grade]}</Tag>
                </Space>}
                description={`企业ID：${item.enterprise_id}`}
              />
              <div style={{ textAlign: 'right', minWidth: 120 }}>
                <div style={{ fontSize: 20, fontWeight: 700, color: GRADE_COLOR[item.grade] }}>
                  {item.total_score}分
                </div>
                <Progress
                  percent={Math.min(100, item.total_score / 10)}
                  showInfo={false} strokeColor={GRADE_COLOR[item.grade]}
                  style={{ width: 100 }}
                />
              </div>
            </List.Item>
          )}
        />
      </Card>

      {/* Record Modal */}
      <Modal title="记录贡献行为" open={recordModal}
        onCancel={() => { setRecordModal(false); form.resetFields() }} footer={null} width={520}>
        <Form form={form} layout="vertical" onFinish={handleRecord} style={{ marginTop: 16 }}>
          <Form.Item name="enterprise_id" label="企业ID" rules={[{ required: true }]}>
            <Input placeholder="请输入企业ID" />
          </Form.Item>
          <Form.Item name="action_type" label="贡献类型" rules={[{ required: true }]}>
            <Select options={ACTION_OPTIONS} placeholder="选择贡献行为类型" />
          </Form.Item>
          <Form.Item name="action_detail" label="贡献行为详情">
            <Input placeholder="如：2026年度会费缴纳" />
          </Form.Item>
          <Form.Item name="action_date" label="发生日期" rules={[{ required: true }]}>
            <Input type="date" />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item style={{ textAlign: 'right', marginBottom: 0 }}>
            <Space>
              <Button onClick={() => { setRecordModal(false); form.resetFields() }}>取消</Button>
              <Button type="primary" htmlType="submit">保存记录</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Query Modal */}
      <Modal title="查询企业贡献分" open={queryModal}
        onCancel={() => { setQueryModal(false); setQueryResult(null) }} footer={null} width={560}>
        <Space.Compact style={{ width: '100%', marginBottom: 16 }}>
          <Input placeholder="输入企业ID" value={queryId} onChange={e => setQueryId(e.target.value)}
            onPressEnter={handleQuery} />
          <Button type="primary" loading={queryLoading} onClick={handleQuery}>查询</Button>
        </Space.Compact>

        {queryResult && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={8}>
                <Statistic title="贡献总分" value={queryResult.total_contribution_score} suffix="分"
                  valueStyle={{ color: GRADE_COLOR[queryResult.grade] }} />
              </Col>
              <Col span={8}>
                <Statistic title="贡献等级" formatter={() =>
                  <Tag color={GRADE_COLOR[queryResult.grade]} style={{ fontSize: 16 }}>
                    {queryResult.grade}级 - {GRADE_LABEL[queryResult.grade]}
                  </Tag>} />
              </Col>
              <Col span={8}>
                <Statistic title="记录数" value={queryResult.record_count} suffix="条" />
              </Col>
            </Row>
            <Card size="small" title="权益说明" style={{ background: '#f6f8ff', marginBottom: 16 }}>
              <p>展示权重倍数：×{queryResult.rights?.display_weight}</p>
              <p>参与评优资格：{queryResult.rights?.priority_award ? '✅ 享有' : '❌ 暂无'}</p>
              <p>理事会选举加分：+{queryResult.rights?.council_bonus}分</p>
            </Card>
            <List size="small" header={<strong>最近贡献记录</strong>}
              dataSource={queryResult.records}
              renderItem={r => (
                <List.Item>
                  <Space>
                    <Tag>{r.action_date}</Tag>
                    <span>{r.action_type}</span>
                    {r.action_detail && <span style={{ color: '#666' }}>- {r.action_detail}</span>}
                  </Space>
                  <Tag color="green">+{r.score_earned}分</Tag>
                </List.Item>
              )}
            />
          </div>
        )}
      </Modal>
    </div>
  )
}
