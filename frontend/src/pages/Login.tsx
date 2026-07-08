import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Form, Input, Button, message, Typography } from 'antd'
import { login, setSession } from '../auth'

const { Title, Text } = Typography

const Login: React.FC = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true)
    try {
      const { token, user } = await login(values.username, values.password)
      setSession(token, user)
      message.success('登录成功')
      navigate('/', { replace: true })
    } catch (e) {
      message.error((e as Error).message || '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#f0f2f5',
      }}
    >
      <Card style={{ width: 380 }}>
        <Title level={3} style={{ textAlign: 'center', marginBottom: 4 }}>
          采购供应链协同平台
        </Title>
        <Text type="secondary" style={{ display: 'block', textAlign: 'center', marginBottom: 24 }}>
          已启用 JWT 认证，请登录后使用
        </Text>
        <Form onFinish={onFinish} initialValues={{ username: 'admin', password: 'admin123' }}>
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input placeholder="用户名" autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password placeholder="密码" autoComplete="current-password" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>
              登录
            </Button>
          </Form.Item>
        </Form>
        <div style={{ fontSize: 12, color: '#999', lineHeight: 1.6 }}>
          演示账号：<br />
          admin / admin123（采购主管）<br />
          buyer / buyer123（采购专员）<br />
          supplier1 / supplier123（供应商管理员）
        </div>
      </Card>
    </div>
  )
}

export default Login

