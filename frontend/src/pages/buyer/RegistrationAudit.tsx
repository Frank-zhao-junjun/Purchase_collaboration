import React, { useEffect, useState } from 'react'
import { Table, Tag, Button, Modal, Form, Input, Descriptions, Space, Card, message } from 'antd'
import { CheckCircleOutlined, CloseCircleOutlined, EyeOutlined } from '@ant-design/icons'
import { getPendingAuditRegistrations, getRegistration, auditRegistration } from '../../api'

const statusMap: Record<string, { color: string; text: string }> = {
  pending_audit: { color: 'orange', text: '待审核' },
  auditing: { color: 'blue', text: '审核中' },
  approved: { color: 'green', text: '已通过' },
  rejected: { color: 'red', text: '已驳回' },
}

const RegistrationAudit: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [detail, setDetail] = useState<any>(null)
  const [auditModalOpen, setAuditModalOpen] = useState(false)
  const [auditTarget, setAuditTarget] = useState<any>(null)
  const [auditAction, setAuditAction] = useState<'approve' | 'reject'>('approve')
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await getPendingAuditRegistrations() as any
      setData(Array.isArray(res) ? res : [])
    } catch { setData([]) }
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const showDetail = async (id: number) => {
    try {
      const res = await getRegistration(id) as any
      setDetail(res)
      setDetailOpen(true)
    } catch { message.error('获取详情失败') }
  }

  const handleAudit = async () => {
    if (!auditTarget) return
    try {
      const values = await form.validateFields()
      await auditRegistration(auditTarget.id, {
        action: auditAction,
        opinion: values.reason || values.opinion || '',
      })
      const msg = auditAction === 'approve'
        ? '已通过，供应商主数据已创建'
        : '已驳回，供应商可修订后重新提交'
      message.success(msg)
      setAuditModalOpen(false)
      form.resetFields()
      fetchData()
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('操作失败')
    }
  }

  const columns = [
    { title: '公司名称', dataIndex: 'company_name', key: 'company_name' },
    { title: '统一社会信用代码', dataIndex: 'unified_credit_code', key: 'unified_credit_code', ellipsis: true },
    { title: '联系人', dataIndex: 'contact_person', key: 'contact_person' },
    { title: '邮箱', dataIndex: 'contact_email', key: 'contact_email' },
    { title: '电话', dataIndex: 'contact_phone', key: 'contact_phone' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => {
      const s = statusMap[v] || { color: 'default', text: v }
      return <Tag color={s.color}>{s.text}</Tag>
    }},
    { title: '提交时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      <Space>
        <Button type="link" icon={<EyeOutlined />} size="small" onClick={() => showDetail(r.id)}>查看</Button>
        <Button type="link" icon={<CheckCircleOutlined />} size="small" style={{ color: '#52c41a' }}
          onClick={() => { setAuditTarget(r); setAuditAction('approve'); setAuditModalOpen(true) }}>通过</Button>
        <Button type="link" danger icon={<CloseCircleOutlined />} size="small"
          onClick={() => { setAuditTarget(r); setAuditAction('reject'); setAuditModalOpen(true) }}>驳回</Button>
      </Space>
    )},
  ]

  return (
    <div>
      <Card title="供应商注册审核 (US-103-1)">
        <Table rowKey="id" dataSource={data} columns={columns} loading={loading} pagination={{ pageSize: 10 }} />
      </Card>

      <Modal title="注册详情 (US-102-2)" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={640}>
        {detail && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="公司名称">{detail.company_name}</Descriptions.Item>
            <Descriptions.Item label="统一社会信用代码">{detail.unified_credit_code}</Descriptions.Item>
            <Descriptions.Item label="联系人">{detail.contact_person}</Descriptions.Item>
            <Descriptions.Item label="邮箱">{detail.contact_email || '-'}</Descriptions.Item>
            <Descriptions.Item label="电话">{detail.contact_phone || '-'}</Descriptions.Item>
            <Descriptions.Item label="主营品类">{detail.main_categories || '-'}</Descriptions.Item>
            <Descriptions.Item label="年供货能力(吨)">{detail.annual_capacity ?? '-'}</Descriptions.Item>
            <Descriptions.Item label="地址">{detail.address || '-'}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusMap[detail.status]?.color}>{statusMap[detail.status]?.text || detail.status}</Tag>
            </Descriptions.Item>
            {detail.invitation?.invitation_code && (
              <Descriptions.Item label="邀请码">{detail.invitation.invitation_code}</Descriptions.Item>
            )}
            {detail.audit_opinion && <Descriptions.Item label="审核意见">{detail.audit_opinion}</Descriptions.Item>}
            <Descriptions.Item label="提交时间">
              {detail.created_at ? new Date(detail.created_at).toLocaleString() : '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <Modal
        title={auditAction === 'approve' ? '通过注册 (US-103-1)' : '驳回注册 (US-103-1)'}
        open={auditModalOpen}
        onOk={handleAudit}
        onCancel={() => { setAuditModalOpen(false); form.resetFields() }}
      >
        <Form form={form} layout="vertical">
          {auditAction === 'reject' && (
            <Form.Item name="reason" label="驳回原因" rules={[{ required: true, message: '请输入驳回原因' }]}>
              <Input.TextArea rows={3} placeholder="请说明驳回原因" />
            </Form.Item>
          )}
          {auditAction === 'approve' && (
            <Form.Item name="reason" label="备注">
              <Input.TextArea rows={2} placeholder="审批备注（可选）" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default RegistrationAudit
