import React, { useEffect, useState } from 'react'
import { Card, Table, Tag, Button, Modal, Form, Input, InputNumber, Select, Descriptions, Tabs, message } from 'antd'
import { PlusOutlined, EyeOutlined, UploadOutlined, ReloadOutlined } from '@ant-design/icons'
import { getInvoices, createInvoice, resubmitInvoice, getPayments } from '../../api'

const SUPPLIER_ID = 1

const SupplierInvoice: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [payments, setPayments] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [resubmitOpen, setResubmitOpen] = useState(false)
  const [detail, setDetail] = useState<any>(null)
  const [resubmitTarget, setResubmitTarget] = useState<any>(null)
  const [form] = Form.useForm()
  const [resubmitForm] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const [invRes, payRes] = await Promise.allSettled([
        getInvoices({ supplier_id: SUPPLIER_ID }),
        getPayments({ supplier_id: SUPPLIER_ID }),
      ])
      setData(invRes.status === 'fulfilled' && Array.isArray(invRes.value) ? invRes.value : [])
      setPayments(payRes.status === 'fulfilled' && Array.isArray(payRes.value) ? payRes.value : [])
    } catch { setData([]) }
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      await createInvoice({
        ...values,
        supplier_id: SUPPLIER_ID,
        invoice_type: values.invoice_type || 'VAT_SPECIAL',
        invoice_image_url: values.invoice_image_url || 'invoice-demo.pdf',
      })
      message.success('发票已创建 (US-403-1)')
      setCreateOpen(false)
      form.resetFields()
      fetchData()
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('创建失败')
    }
  }

  const openResubmit = (row: any) => {
    setResubmitTarget(row)
    resubmitForm.setFieldsValue({
      amount: row.amount,
      tax_amount: row.tax_amount,
      statement_id: row.statement_id,
      remarks: row.remarks,
    })
    setResubmitOpen(true)
  }

  const handleResubmit = async () => {
    if (!resubmitTarget) return
    try {
      const values = await resubmitForm.validateFields()
      await resubmitInvoice(resubmitTarget.id, {
        supplier_id: SUPPLIER_ID,
        statement_id: values.statement_id,
        amount: values.amount,
        tax_amount: values.tax_amount,
        remarks: values.remarks,
        invoice_image_url: values.invoice_image_url || 'invoice-resubmit-demo.pdf',
      })
      message.success('发票已重提 (US-404-1)')
      setResubmitOpen(false)
      fetchData()
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('重提失败')
    }
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    issued: { color: 'blue', text: '已开票' },
    verified: { color: 'green', text: '已认证' },
    rejected: { color: 'red', text: '已驳回' },
  }

  const paymentStatusMap: Record<string, { color: string; text: string }> = {
    applied: { color: 'orange', text: '申请中' },
    approved: { color: 'blue', text: '已批准' },
    paid: { color: 'green', text: '已付款' },
  }

  const columns = [
    { title: '发票号', dataIndex: 'invoice_no', key: 'invoice_no' },
    { title: '价税合计', dataIndex: 'total_amount', key: 'total_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => {
      const s = statusMap[v] || { color: 'default', text: v }
      return <Tag color={s.color}>{s.text}</Tag>
    }},
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      <>
        <Button type="link" icon={<EyeOutlined />} size="small" onClick={() => { setDetail(r); setDetailOpen(true) }}>查看</Button>
        {r.status === 'rejected' && (
          <Button type="link" icon={<ReloadOutlined />} size="small" onClick={() => openResubmit(r)}>重提 (US-404-1)</Button>
        )}
      </>
    )},
  ]

  const paymentColumns = [
    { title: '付款单号', dataIndex: 'payment_no', key: 'payment_no' },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => `¥${(v || 0).toLocaleString()}` },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => {
      const s = paymentStatusMap[v] || { color: 'default', text: v }
      return <Tag color={s.color}>{s.text}</Tag>
    }},
    { title: '预计付款', dataIndex: 'expected_date', key: 'expected_date', render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
  ]

  return (
    <div>
      <Card title="财务协同 (Phase 4)">
        <Tabs items={[
          {
            key: 'invoices',
            label: '发票 (US-403-1)',
            children: (
              <>
                <div style={{ marginBottom: 16, textAlign: 'right' }}>
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>创建发票</Button>
                </div>
                <Table rowKey="id" dataSource={data} columns={columns} loading={loading} pagination={{ pageSize: 10 }} />
              </>
            ),
          },
          {
            key: 'payments',
            label: '付款查询 (US-405-2)',
            children: <Table rowKey="id" dataSource={payments} columns={paymentColumns} loading={loading} pagination={{ pageSize: 10 }} />,
          },
        ]} />
      </Card>

      <Modal title="创建发票 (US-403-1)" open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); form.resetFields() }} width={560}>
        <Form form={form} layout="vertical">
          <Form.Item name="statement_id" label="关联结算单ID" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} placeholder="已确认的结算单 ID" />
          </Form.Item>
          <Form.Item name="amount" label="金额（不含税）" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
          </Form.Item>
          <Form.Item name="tax_amount" label="税额" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
          </Form.Item>
          <Form.Item name="invoice_type" label="发票类型" initialValue="VAT_SPECIAL">
            <Select>
              <Select.Option value="VAT_SPECIAL">增值税专用发票</Select.Option>
              <Select.Option value="VAT_NORMAL">增值税普通发票</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label="发票影像">
            <Button icon={<UploadOutlined />} onClick={() => form.setFieldValue('invoice_image_url', 'invoice-demo.pdf')}>模拟上传</Button>
          </Form.Item>
          <Form.Item name="invoice_image_url" hidden><Input /></Form.Item>
          <Form.Item name="remarks" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="重提发票 (US-404-1)" open={resubmitOpen} onOk={handleResubmit} onCancel={() => setResubmitOpen(false)} width={560} okText="重新提交">
        {resubmitTarget?.rejection_reason && (
          <p style={{ color: '#cf1322', marginBottom: 12 }}>驳回原因：{resubmitTarget.rejection_reason}</p>
        )}
        <Form form={resubmitForm} layout="vertical">
          <Form.Item name="statement_id" label="关联结算单ID">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="amount" label="修订金额" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
          </Form.Item>
          <Form.Item name="tax_amount" label="修订税额" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
          </Form.Item>
          <Form.Item label="补充附件">
            <Button icon={<UploadOutlined />} onClick={() => resubmitForm.setFieldValue('invoice_image_url', 'invoice-resubmit-demo.pdf')}>模拟上传</Button>
          </Form.Item>
          <Form.Item name="invoice_image_url" hidden><Input /></Form.Item>
          <Form.Item name="remarks" label="补充说明">
            <Input.TextArea rows={2} placeholder="按驳回原因补充说明" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="发票详情" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={600}>
        {detail && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="发票号">{detail.invoice_no}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusMap[detail.status]?.color}>{statusMap[detail.status]?.text || detail.status}</Tag></Descriptions.Item>
            <Descriptions.Item label="金额">¥{(detail.amount || 0).toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label="税额">¥{(detail.tax_amount || 0).toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label="关联结算单">{detail.statement_id || '-'}</Descriptions.Item>
            <Descriptions.Item label="影像">{detail.invoice_image_url || '-'}</Descriptions.Item>
            {detail.rejection_reason && <Descriptions.Item label="驳回原因" span={2}>{detail.rejection_reason}</Descriptions.Item>}
            {detail.remarks && <Descriptions.Item label="备注" span={2}>{detail.remarks}</Descriptions.Item>}
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default SupplierInvoice
