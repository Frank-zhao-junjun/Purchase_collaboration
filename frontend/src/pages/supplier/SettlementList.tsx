import React, { useEffect, useState } from 'react'
import { Card, Table, Tag, Button, Modal, Form, Input, InputNumber, Descriptions, message, Statistic, Row, Col } from 'antd'
import { PlusOutlined, EyeOutlined, EditOutlined } from '@ant-design/icons'
import { getStatements, createStatement, updateStatement, getStatementStats } from '../../api'

const SUPPLIER_ID = 1

const SupplierSettlement: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [detail, setDetail] = useState<any>(null)
  const [editTarget, setEditTarget] = useState<any>(null)
  const [stats, setStats] = useState<any>({})
  const [form] = Form.useForm()
  const [editForm] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const [stmtRes, statsRes] = await Promise.allSettled([
        getStatements({ supplier_id: SUPPLIER_ID }),
        getStatementStats()
      ])
      setData(stmtRes.status === 'fulfilled' ? (Array.isArray(stmtRes.value) ? stmtRes.value : []) : [])
      setStats(statsRes.status === 'fulfilled' ? (statsRes.value as any) || {} : {})
    } catch { setData([]) }
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      await createStatement({ ...values, supplier_id: SUPPLIER_ID, receipt_ids: [1] }, true)
      message.success('结算单已提交，等待采购方审核 (US-401-1)')
      setCreateOpen(false)
      form.resetFields()
      fetchData()
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('创建失败')
    }
  }

  const openEdit = (row: any) => {
    setEditTarget(row)
    editForm.setFieldsValue({
      period_start: row.period_start?.slice?.(0, 10) || row.period_start,
      period_end: row.period_end?.slice?.(0, 10) || row.period_end,
      total_amount: row.total_amount,
      remarks: row.remarks,
    })
    setEditOpen(true)
  }

  const handleEditSubmit = async () => {
    if (!editTarget) return
    try {
      const values = await editForm.validateFields()
      await updateStatement(editTarget.id, {
        supplier_id: SUPPLIER_ID,
        period_start: values.period_start,
        period_end: values.period_end,
        total_amount: values.total_amount,
        remarks: values.remarks,
      }, true)
      message.success('结算单已修订并重新提交 (US-402-1)')
      setEditOpen(false)
      fetchData()
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('提交失败')
    }
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    draft: { color: 'default', text: '草稿' },
    pending_audit: { color: 'orange', text: '待审核' },
    confirmed: { color: 'green', text: '已确认' },
    rejected: { color: 'red', text: '已驳回' },
  }

  const columns = [
    { title: '结算单号', dataIndex: 'statement_no', key: 'statement_no' },
    { title: '结算期间', key: 'period', render: (_: any, r: any) => `${r.period_start || ''} ~ ${r.period_end || ''}` },
    { title: '金额', dataIndex: 'total_amount', key: 'total_amount', render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => {
      const s = statusMap[v] || { color: 'default', text: v }
      return <Tag color={s.color}>{s.text}</Tag>
    }},
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      <>
        <Button type="link" icon={<EyeOutlined />} size="small" onClick={() => { setDetail(r); setDetailOpen(true) }}>查看</Button>
        {(r.status === 'rejected' || r.status === 'confirmed') && (
          <Button type="link" icon={<EditOutlined />} size="small" onClick={() => openEdit(r)}>修订 (US-402-1)</Button>
        )}
      </>
    )},
  ]

  return (
    <div>
      <Card title="结算单 (US-401-1 / US-402-1)" extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>创建并提交结算单</Button>
      }>
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}><Statistic title="待审核" value={stats.pending_count || 0} /></Col>
          <Col span={6}><Statistic title="已确认" value={stats.confirmed_count || 0} /></Col>
        </Row>
        <Table rowKey="id" dataSource={data} columns={columns} loading={loading} pagination={{ pageSize: 10 }} />
      </Card>

      <Modal title="创建结算单 (US-401-1)" open={createOpen} onOk={handleCreate} onCancel={() => { setCreateOpen(false); form.resetFields() }} width={560} okText="提交审核">
        <Form form={form} layout="vertical">
          <Form.Item name="period_start" label="结算开始日期" rules={[{ required: true }]}>
            <Input type="date" />
          </Form.Item>
          <Form.Item name="period_end" label="结算结束日期" rules={[{ required: true }]}>
            <Input type="date" />
          </Form.Item>
          <Form.Item name="total_amount" label="结算金额" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} prefix="¥" placeholder="结算金额" />
          </Form.Item>
          <Form.Item name="remarks" label="备注">
            <Input.TextArea rows={2} placeholder="对账说明" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="修订结算单 (US-402-1)" open={editOpen} onOk={handleEditSubmit} onCancel={() => setEditOpen(false)} width={560} okText="重新提交">
        <Form form={editForm} layout="vertical">
          <Form.Item name="period_start" label="结算开始日期" rules={[{ required: true }]}>
            <Input type="date" />
          </Form.Item>
          <Form.Item name="period_end" label="结算结束日期" rules={[{ required: true }]}>
            <Input type="date" />
          </Form.Item>
          <Form.Item name="total_amount" label="结算金额" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} prefix="¥" />
          </Form.Item>
          <Form.Item name="remarks" label="修订说明">
            <Input.TextArea rows={2} placeholder="根据采购方意见修订" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="结算单详情" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={600}>
        {detail && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="结算单号">{detail.statement_no}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color={statusMap[detail.status]?.color}>{statusMap[detail.status]?.text || detail.status}</Tag></Descriptions.Item>
            <Descriptions.Item label="结算期间" span={2}>{detail.period_start} ~ {detail.period_end}</Descriptions.Item>
            <Descriptions.Item label="总金额">¥{(detail.total_amount || 0).toLocaleString()}</Descriptions.Item>
            <Descriptions.Item label="已付金额">¥{(detail.paid_amount || 0).toLocaleString()}</Descriptions.Item>
            {detail.remarks && <Descriptions.Item label="备注" span={2}>{detail.remarks}</Descriptions.Item>}
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default SupplierSettlement
