import React, { useEffect, useState } from 'react'
import { Card, Table, Tag, Button, Input, Space, message } from 'antd'
import { MailOutlined, SendOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { getInvitations } from '../../api'

const EMAIL_KEY = 'xijiu_supplier_invited_email'

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'orange', text: '待注册' },
  accepted: { color: 'green', text: '已注册' },
  expired: { color: 'default', text: '已过期' },
  cancelled: { color: 'red', text: '已取消' },
}

const RegistrationInvitationList: React.FC = () => {
  const navigate = useNavigate()
  const [email, setEmail] = useState(() => sessionStorage.getItem(EMAIL_KEY) || '')
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const fetchData = async (targetEmail?: string) => {
    const q = (targetEmail ?? email).trim()
    if (!q) {
      message.warning('请输入采购方邀请时填写的邮箱')
      return
    }
    setLoading(true)
    try {
      const res = await getInvitations({ email: q }) as any
      setData(Array.isArray(res) ? res : [])
      sessionStorage.setItem(EMAIL_KEY, q)
    } catch {
      setData([])
      message.error('加载失败')
    }
    setLoading(false)
  }

  useEffect(() => {
    if (email.trim()) fetchData(email.trim())
  }, [])

  const columns = [
    { title: '邀请码', dataIndex: 'invitation_code', key: 'invitation_code', render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: '受邀企业', dataIndex: 'invited_supplier_name', key: 'invited_supplier_name' },
    { title: '联系人', dataIndex: 'invited_contact_person', key: 'invited_contact_person' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => {
      const s = statusMap[v] || { color: 'default', text: v }
      return <Tag color={s.color}>{s.text}</Tag>
    }},
    { title: '有效期至', dataIndex: 'expiry_date', key: 'expiry_date', render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
    { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true },
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      r.status === 'pending' ? (
        <Button
          type="link"
          size="small"
          onClick={() => navigate(`/supplier/registration?code=${r.invitation_code}`)}
        >
          去注册
        </Button>
      ) : null
    )},
  ]

  return (
    <Card title="注册邀请 (US-101-2)" extra={<SendOutlined style={{ color: '#52c41a' }} />}>
      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          prefix={<MailOutlined />}
          placeholder="输入受邀邮箱查看邀请"
          value={email}
          onChange={e => setEmail(e.target.value)}
          onPressEnter={() => fetchData()}
          style={{ width: 320 }}
        />
        <Button type="primary" onClick={() => fetchData()} loading={loading}>查询</Button>
      </Space>
      <Table rowKey="id" dataSource={data} columns={columns} loading={loading} pagination={{ pageSize: 10 }} />
    </Card>
  )
}

export default RegistrationInvitationList
