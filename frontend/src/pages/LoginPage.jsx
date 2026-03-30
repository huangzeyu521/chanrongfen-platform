import React, { useState } from 'react'
import { Form, Input, Button, Card, Typography, message, Space } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'

const { Title, Text } = Typography

export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const login = useAuthStore(s => s.login)

  const onFinish = async (values) => {
    setLoading(true)
    try {
      await login(values.username, values.password)
      message.success('登录成功')
      navigate('/', { replace: true })
    } catch (err) {
      message.error(err?.detail || '登录失败，请检查用户名和密码')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', background: 'linear-gradient(135deg, #1F4E79 0%, #2E75B6 50%, #5BA4CF 100%)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24
    }}>
      <Card style={{ width: 420, borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.3)' }}>
        <Space direction="vertical" style={{ width: '100%', textAlign: 'center', marginBottom: 32 }}>
          <Title level={2} style={{ color: '#1F4E79', margin: 0 }}>产融分平台</Title>
          <Text type="secondary">商协会数字化产融对接管理系统</Text>
        </Space>

        <Form name="login" onFinish={onFinish} size="large" autoComplete="off">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block style={{ height: 44 }}>
              登 录
            </Button>
          </Form.Item>
        </Form>

        <Text type="secondary" style={{ fontSize: 12 }}>
          默认管理员账号：admin / Admin@123
        </Text>
      </Card>
    </div>
  )
}
