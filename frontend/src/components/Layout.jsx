import React, { useState } from 'react'
import { Layout, Menu, Avatar, Dropdown, Typography, Space, Button } from 'antd'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined, BankOutlined, UserOutlined, EnvironmentOutlined,
  SwapOutlined, TrophyOutlined, LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined
} from '@ant-design/icons'
import useAuthStore from '../store/authStore'

const { Header, Sider, Content } = Layout
const { Text } = Typography

const menuItems = [
  { key: '/dashboard',   icon: <DashboardOutlined />,  label: '数据看板' },
  { key: '/enterprises', icon: <BankOutlined />,        label: '企业管理' },
  { key: '/experts',     icon: <UserOutlined />,        label: '专家管理' },
  { key: '/regions',     icon: <EnvironmentOutlined />, label: '区域需求' },
  { key: '/dockings',    icon: <SwapOutlined />,        label: '对接管理' },
  { key: '/members',     icon: <TrophyOutlined />,      label: '会员贡献' },
]

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()

  const userMenu = {
    items: [
      { key: 'logout', icon: <LogoutOutlined />, label: '退出登录',
        onClick: () => { logout(); navigate('/login') } }
    ]
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        theme="dark"
        style={{ background: '#001529' }}
      >
        <div style={{
          height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: '#002140', color: '#fff', fontSize: collapsed ? 14 : 18, fontWeight: 700
        }}>
          {collapsed ? '产融' : '产融分平台'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ marginTop: 8 }}
        />
      </Sider>

      <Layout>
        <Header style={{
          padding: '0 24px', background: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          boxShadow: '0 1px 4px rgba(0,21,41,0.08)'
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16, width: 40, height: 40 }}
          />
          <Dropdown menu={userMenu}>
            <Space style={{ cursor: 'pointer' }}>
              <Avatar style={{ background: '#1677ff' }} icon={<UserOutlined />} />
              <Text>{user?.username}</Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {user?.role === 'admin' ? '管理员' : user?.role}
              </Text>
            </Space>
          </Dropdown>
        </Header>

        <Content style={{ margin: '24px', background: '#f0f2f5' }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
