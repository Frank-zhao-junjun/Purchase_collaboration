import React, { useEffect, useState } from 'react'
import {
  Table, Button, Modal, Form, Input, InputNumber, Tag, Space, message,
  Popconfirm, Card, Typography, Descriptions,
} from 'antd'
import { PlusOutlined, DeleteOutlined, MailOutlined, LinkOutlined, CopyOutlined } from '@ant-design/icons'
import { getInvitations, createInvitation, deleteInvitation } from '../../api'

const { Text, Paragraph } = Typography

const statusMap: Record<string, { color: string; text: string }> = {
  pending: { color: 'orange', text: '待响应' },
  accepted: { color: 'green', text: '已注册' },
  expired: { color: 'default', text: '已过期' },
  cancelled: { color: 'red', text: '已取消' },
}

function buildRegistrationLink(code: string) {
  return `${window.location.origin}/supplier/registration?code=${encodeURIComponent(code)}`
}

async function copyText(label: string, text: string) {
  try {
    await navigator.clipboard.writeText(text)
    message.success(`${label}已复制`)
  } catch {
    message.error('复制失败，请手动选择复制')
  }
}

const InvitationList: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [successOpen, setSuccessOpen] = useState(false)
  const [createdInvite, setCreatedInvite] = useState<any>(null)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await getInvitations() as any
      setData(Array.isArray(res) ? res : [])
    } catch { setData([]) }
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      const res = await createInvitation(values) as any
      setCreatedInvite(res)
      setModalOpen(false)
      form.resetFields()
      setSuccessOpen(true)
      fetchData()
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('操作失败')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteInvitation(id)
      message.success('已取消')
      fetchData()
    } catch { message.error('取消失败') }
  }

  const registrationLink = createdInvite?.invitation_code
    ? buildRegistrationLink(createdInvite.invitation_code)
    : ''

  const columns = [
    { title: '邀请码', dataIndex: 'invitation_code', key: 'invitation_code', render: (v: string) => <Tag color="blue">{v}</Tag> },
    { title: '供应商名称', dataIndex: 'invited_supplier_name', key: 'invited_supplier_name' },
    { title: '联系人', dataIndex: 'invited_contact_person', key: 'invited_contact_person' },
    { title: '邮箱', dataIndex: 'invited_email', key: 'invited_email' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => {
      const s = statusMap[v] || { color: 'default', text: v }
      return <Tag color={s.color}>{s.text}</Tag>
    }},
    { title: '有效期至', dataIndex: 'expiry_date', key: 'expiry_date', render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
    { title: '备注', dataIndex: 'notes', key: 'notes', ellipsis: true },
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      <Space>
        {r.status === 'pending' && (
          <Button
            type="link"
            size="small"
            icon={<LinkOutlined />}
            onClick={() => copyText('注册链接', buildRegistrationLink(r.invitation_code))}
          >
            复制链接
          </Button>
        )}
        <Popconfirm title="确定取消此邀请？" onConfirm={() => handleDelete(r.id)}>
          <Button type="link" danger icon={<DeleteOutlined />} size="small">取消</Button>
        </Popconfirm>
      </Space>
    )},
  ]

  return (
    <div>
      <Card title="供应商注册邀请 (US-101)" extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>发起邀请</Button>
      }>
        <Table rowKey="id" dataSource={data} columns={columns} loading={loading} pagination={{ pageSize: 10 }} />
      </Card>

      <Modal
        title="发起注册邀请"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        width={520}
        okText="发送邀请"
      >
        <Form form={form} layout="vertical" initialValues={{ expiry_days: 7 }}>
          <Form.Item name="invited_supplier_name" label="供应商名称" rules={[{ required: true, message: '请输入供应商名称' }]}>
            <Input placeholder="请输入供应商名称" />
          </Form.Item>
          <Form.Item name="invited_email" label="邮箱" rules={[{ required: true, type: 'email', message: '请输入有效邮箱' }]}>
            <Input prefix={<MailOutlined />} placeholder="name@company.com" />
          </Form.Item>
          <Form.Item name="invited_contact_person" label="联系人">
            <Input placeholder="联系人姓名" />
          </Form.Item>
          <Form.Item name="expiry_days" label="有效天数" rules={[{ required: true, message: '请输入有效天数' }]}>
            <InputNumber min={1} max={90} style={{ width: '100%' }} addonAfter="天" />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={2} placeholder="邀请说明" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="邀请已创建 — 请发送注册链接"
        open={successOpen}
        onCancel={() => setSuccessOpen(false)}
        footer={[
          <Button key="copy-link" type="primary" icon={<CopyOutlined />} onClick={() => copyText('注册链接', registrationLink)}>
            复制注册链接
          </Button>,
          <Button key="close" onClick={() => setSuccessOpen(false)}>关闭</Button>,
        ]}
        width={560}
      >
        {createdInvite && (
          <>
            <Paragraph type="secondary">
              请将下方邀请码或注册链接发送给供应商 <Text strong>{createdInvite.invited_email}</Text>。
            </Paragraph>
            <Descriptions bordered column={1} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="邀请码">
                <Text copyable>{createdInvite.invitation_code}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="注册链接">
                <Text copyable style={{ wordBreak: 'break-all' }}>{registrationLink}</Text>
              </Descriptions.Item>
              <Descriptions.Item label="有效期至">
                {createdInvite.expiry_date ? new Date(createdInvite.expiry_date).toLocaleString() : '-'}
              </Descriptions.Item>
            </Descriptions>
          </>
        )}
      </Modal>
    </div>
  )
}

export default InvitationList
