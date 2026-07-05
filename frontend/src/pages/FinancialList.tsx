import React, { useEffect, useState } from 'react'
import { Table, Card, Button, Space, Tag, Row, Col, Statistic, Tabs, Modal, message, Input, Descriptions } from 'antd'
import { FileTextOutlined, DollarOutlined, CreditCardOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import {
  getStatements, getStatementStats, getStatement,
  buyerAuditStatement, addStatementComment,
  getInvoices, getInvoiceStats, getInvoice,
  threeWayMatch, approveInvoice, rejectInvoice,
  getPayments, getPaymentStats, approvePayment, confirmPayment,
  SettlementStatement, Invoice, Payment
} from '../api'

const statementStatusMap: Record<string, { color: string; text: string }> = {
  draft: { color: 'default', text: '草稿' },
  pending_audit: { color: 'orange', text: '待审核' },
  rejected: { color: 'red', text: '已驳回' },
  confirmed: { color: 'blue', text: '已确认' },
  paid: { color: 'green', text: '已付款' },
  partial: { color: 'orange', text: '部分付款' },
}

const invoiceStatusMap: Record<string, { color: string; text: string }> = {
  issued: { color: 'blue', text: '已开票' },
  verified: { color: 'green', text: '已认证' },
  rejected: { color: 'red', text: '已驳回' },
  void: { color: 'default', text: '已作废' },
}

const paymentStatusMap: Record<string, { color: string; text: string }> = {
  applied: { color: 'orange', text: '申请中' },
  approved: { color: 'blue', text: '已批准' },
  paid: { color: 'green', text: '已付款' },
  rejected: { color: 'red', text: '已拒绝' },
}

const FinancialList: React.FC = () => {
  const [activeTab, setActiveTab] = useState('statements')
  const [statements, setStatements] = useState<SettlementStatement[]>([])
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(false)
  const [statementStats, setStatementStats] = useState<any>(null)
  const [invoiceStats, setInvoiceStats] = useState<any>(null)
  const [paymentStats, setPaymentStats] = useState<any>(null)
  const [auditOpen, setAuditOpen] = useState(false)
  const [auditTarget, setAuditTarget] = useState<SettlementStatement | null>(null)
  const [auditMessage, setAuditMessage] = useState('')
  const [matchOpen, setMatchOpen] = useState(false)
  const [matchResult, setMatchResult] = useState<any>(null)
  const [invoiceDetail, setInvoiceDetail] = useState<Invoice | null>(null)

  const reloadAll = () => {
    loadStatements()
    loadStatementStats()
    loadInvoices()
    loadInvoiceStats()
    loadPayments()
    loadPaymentStats()
  }

  useEffect(() => { reloadAll() }, [])

  const loadStatements = async () => {
    setLoading(true)
    try {
      setStatements(await getStatements() as SettlementStatement[])
    } catch { message.error('加载结算单失败') }
    finally { setLoading(false) }
  }

  const loadStatementStats = async () => {
    try { setStatementStats(await getStatementStats()) } catch { /* ignore */ }
  }

  const loadInvoices = async () => {
    try { setInvoices(await getInvoices() as Invoice[]) } catch { message.error('加载发票失败') }
  }

  const loadInvoiceStats = async () => {
    try { setInvoiceStats(await getInvoiceStats()) } catch { /* ignore */ }
  }

  const loadPayments = async () => {
    try { setPayments(await getPayments() as Payment[]) } catch { message.error('加载付款记录失败') }
  }

  const loadPaymentStats = async () => {
    try { setPaymentStats(await getPaymentStats()) } catch { /* ignore */ }
  }

  const handleAudit = async (action: 'approve' | 'reject') => {
    if (!auditTarget) return
    try {
      await buyerAuditStatement(auditTarget.id, {
        action,
        auditor: '采购员',
        message: auditMessage || (action === 'approve' ? 'US-401-2/402-2' : '需修订'),
      })
      if (auditMessage.trim()) {
        await addStatementComment(auditTarget.id, { author: '采购员', comment: auditMessage })
      }
      message.success(action === 'approve' ? '结算单已批准' : '结算单已驳回')
      setAuditOpen(false)
      setAuditMessage('')
      reloadAll()
    } catch { message.error('审核失败') }
  }

  const handleThreeWayMatch = async (invoice: Invoice) => {
    try {
      const res = await threeWayMatch(invoice.id) as any
      const detail = await getInvoice(invoice.id) as Invoice
      setInvoiceDetail(detail)
      setMatchResult(res)
      setMatchOpen(true)
    } catch { message.error('三单匹配失败') }
  }

  const handleApproveInvoice = async (id: number) => {
    try {
      await approveInvoice(id)
      message.success('发票已批准')
      reloadAll()
    } catch { message.error('批准失败') }
  }

  const handleRejectInvoice = async (id: number) => {
    Modal.confirm({
      title: '驳回发票',
      content: (
        <Input.TextArea id="reject-reason" rows={3} placeholder="驳回原因" defaultValue="金额或附件不符" />
      ),
      onOk: async () => {
        const el = document.getElementById('reject-reason') as HTMLTextAreaElement | null
        await rejectInvoice(id, el?.value || '驳回')
        message.success('发票已驳回')
        reloadAll()
      },
    })
  }

  const handleApprovePayment = async (id: number) => {
    try {
      await approvePayment(id)
      message.success('付款申请已批准')
      reloadAll()
    } catch { message.error('操作失败') }
  }

  const handleConfirmPayment = async (id: number) => {
    try {
      await confirmPayment(id)
      message.success('付款已完成')
      reloadAll()
    } catch { message.error('操作失败') }
  }

  const statementColumns: ColumnsType<SettlementStatement> = [
    { title: '结算单号', dataIndex: 'statement_no', key: 'statement_no', width: 160 },
    { title: '供应商', dataIndex: 'supplier_name', key: 'supplier_name', width: 150 },
    { title: '结算周期', key: 'period', width: 200, render: (_, r) => `${new Date(r.period_start).toLocaleDateString()} ~ ${new Date(r.period_end).toLocaleDateString()}` },
    { title: '结算金额', dataIndex: 'total_amount', key: 'total_amount', width: 120, render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <Tag color={statementStatusMap[v]?.color}>{statementStatusMap[v]?.text || v}</Tag> },
    { title: '操作', key: 'action', width: 180, render: (_, r) => r.status === 'pending_audit' ? (
      <Space>
        <Button type="link" onClick={() => { setAuditTarget(r); setAuditOpen(true) }}>审核 (US-401-2)</Button>
        <Button type="link" onClick={async () => {
          const detail = await getStatement(r.id) as SettlementStatement
          Modal.info({ title: '结算单详情', width: 560, content: (
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="备注">{detail.remarks || '-'}</Descriptions.Item>
              <Descriptions.Item label="金额">¥{detail.total_amount}</Descriptions.Item>
            </Descriptions>
          ) })
        }}>查看</Button>
      </Space>
    ) : <span style={{ color: '#999' }}>-</span> },
  ]

  const invoiceColumns: ColumnsType<Invoice> = [
    { title: '发票号', dataIndex: 'invoice_no', key: 'invoice_no', width: 160 },
    { title: '供应商', dataIndex: 'supplier_name', key: 'supplier_name', width: 150 },
    { title: '价税合计', dataIndex: 'total_amount', key: 'total_amount', width: 120, render: (v: number) => `¥${(v || 0).toLocaleString()}` },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <Tag color={invoiceStatusMap[v]?.color}>{invoiceStatusMap[v]?.text || v}</Tag> },
    { title: '操作', key: 'action', width: 260, render: (_, r) => (
      <Space wrap>
        <Button type="link" onClick={() => handleThreeWayMatch(r)}>三单匹配 (US-403-2)</Button>
        {r.status === 'issued' && (
          <>
            <Button type="link" onClick={() => handleApproveInvoice(r.id)}>批准</Button>
            <Button type="link" danger onClick={() => handleRejectInvoice(r.id)}>驳回</Button>
          </>
        )}
        {r.status === 'issued' && <Button type="link" onClick={async () => {
          const detail = await getInvoice(r.id) as Invoice
          Modal.info({ title: '重提发票 (US-404-2)', content: `金额 ¥${detail.amount}，状态 ${detail.status}` })
        }}>查看重提</Button>}
      </Space>
    )},
  ]

  const paymentColumns: ColumnsType<Payment> = [
    { title: '付款单号', dataIndex: 'payment_no', key: 'payment_no', width: 160 },
    { title: '供应商', dataIndex: 'supplier_name', key: 'supplier_name', width: 150 },
    { title: '付款金额', dataIndex: 'amount', key: 'amount', width: 120, render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <Tag color={paymentStatusMap[v]?.color}>{paymentStatusMap[v]?.text || v}</Tag> },
    { title: '操作', key: 'action', width: 150, render: (_, r) => (
      <Space>
        {r.status === 'applied' && <Button type="link" onClick={() => handleApprovePayment(r.id)}>批准 (US-405-1)</Button>}
        {r.status === 'approved' && <Button type="link" onClick={() => handleConfirmPayment(r.id)}>确认付款</Button>}
      </Space>
    )},
  ]

  const tabItems = [
    {
      key: 'statements',
      label: <span><FileTextOutlined /> 结算单</span>,
      children: (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}><Card bordered={false} size="small"><Statistic title="待审核" value={statementStats?.pending_count || 0} suffix="单" valueStyle={{ color: '#FAAD14' }} /></Card></Col>
            <Col span={6}><Card bordered={false} size="small"><Statistic title="已确认" value={statementStats?.confirmed_count || 0} suffix="单" valueStyle={{ color: '#1890FF' }} /></Card></Col>
            <Col span={6}><Card bordered={false} size="small"><Statistic title="已付款" value={statementStats?.paid_count || 0} suffix="单" valueStyle={{ color: '#52C41A' }} /></Card></Col>
          </Row>
          <Table columns={statementColumns} dataSource={statements} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
        </>
      ),
    },
    {
      key: 'invoices',
      label: <span><DollarOutlined /> 发票</span>,
      children: (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}><Card bordered={false} size="small"><Statistic title="待认证" value={invoiceStats?.issued_count || 0} suffix="张" valueStyle={{ color: '#FAAD14' }} /></Card></Col>
            <Col span={6}><Card bordered={false} size="small"><Statistic title="已认证" value={invoiceStats?.verified_count || 0} suffix="张" valueStyle={{ color: '#52C41A' }} /></Card></Col>
          </Row>
          <Table columns={invoiceColumns} dataSource={invoices} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
        </>
      ),
    },
    {
      key: 'payments',
      label: <span><CreditCardOutlined /> 付款</span>,
      children: (
        <>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}><Card bordered={false} size="small"><Statistic title="申请中" value={paymentStats?.applied_count || 0} suffix="笔" valueStyle={{ color: '#FAAD14' }} /></Card></Col>
            <Col span={6}><Card bordered={false} size="small"><Statistic title="已付款" value={paymentStats?.paid_count || 0} suffix="笔" valueStyle={{ color: '#52C41A' }} /></Card></Col>
          </Row>
          <Table columns={paymentColumns} dataSource={payments} rowKey="id" loading={loading} pagination={{ pageSize: 10 }} />
        </>
      ),
    },
  ]

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 16 }}>财务管理 (Phase 4)</h2>
      <Card bordered={false}>
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
      </Card>

      <Modal title="审核结算单 (US-401-2 / US-402-2)" open={auditOpen} onCancel={() => setAuditOpen(false)} footer={[
        <Button key="reject" danger onClick={() => handleAudit('reject')}>驳回</Button>,
        <Button key="approve" type="primary" onClick={() => handleAudit('approve')}>批准</Button>,
      ]}>
        <p>结算单：{auditTarget?.statement_no}</p>
        <Input.TextArea rows={3} placeholder="审核留言" value={auditMessage} onChange={(e) => setAuditMessage(e.target.value)} />
      </Modal>

      <Modal title="三单匹配结果 (US-403-2)" open={matchOpen} onCancel={() => setMatchOpen(false)} footer={null}>
        {matchResult && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="匹配结果">
              <Tag color={matchResult.matched ? 'green' : 'red'}>{matchResult.matched ? '匹配' : '差异'}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="发票金额">¥{matchResult.invoice_total}</Descriptions.Item>
            <Descriptions.Item label="结算单金额">¥{matchResult.statement_amount}</Descriptions.Item>
            <Descriptions.Item label="收货参考">¥{matchResult.receipt_amount}</Descriptions.Item>
            {invoiceDetail && <Descriptions.Item label="发票状态">{invoiceDetail.status}</Descriptions.Item>}
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default FinancialList
