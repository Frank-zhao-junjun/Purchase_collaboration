import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, List, Tag, Button } from 'antd'
import { MessageOutlined, SwapOutlined, TrophyOutlined, RightOutlined, FundProjectionScreenOutlined, ScheduleOutlined, SendOutlined, AccountBookOutlined, FileSearchOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { getSupplierOrders, getForecasts, getDeliveryPlans, getASNList, getStatements, getInvoices } from '../../api'

const SUPPLIER_ID = 1

const SupplierHome: React.FC = () => {
  const navigate = useNavigate()
  const [stats, setStats] = useState({
    pendingInvitations: 1,
    pendingOrders: 0,
    pendingDeliveryPlans: 0,
    pendingSettlements: 0,
    pendingInvoices: 0,
  })

  const quickActions = [
    { icon: <SendOutlined />, label: '注册邀请', color: '#52c41a', path: '/supplier/registration-invitations' },
    { icon: <MessageOutlined />, label: '寻源邀请', color: '#3E5BF2', path: '/supplier/invitations' },
    { icon: <SwapOutlined />, label: '投标管理', color: '#FA8C16', path: '/supplier/bids' },
    { icon: <TrophyOutlined />, label: '合同管理', color: '#52c41a', path: '/supplier/contracts' },
    { icon: <FundProjectionScreenOutlined />, label: '产能响应', color: '#13c2c2', path: '/supplier/capacity' },
    { icon: <ScheduleOutlined />, label: '要货计划', color: '#2f54eb', path: '/supplier/delivery-plans' },
    { icon: <SendOutlined />, label: '送货计划ASN', color: '#722ed1', path: '/supplier/asn' },
    { icon: <AccountBookOutlined />, label: '结算单', color: '#eb2f96', path: '/supplier/settlements' },
    { icon: <FileSearchOutlined />, label: '发票管理', color: '#fa8c16', path: '/supplier/invoices' },
  ]

  const todos = [
    { id: 1, text: '收到「2026年红缨子糯高粱采购寻源」邀请', type: 'invitation', status: 'pending' },
    { id: 2, text: '合同「2026年糯高粱采购合同」待签署', type: 'contract', status: 'pending' },
  ]

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [ordersRes, forecastsRes, plansRes, asnRes, statementsRes, invoicesRes] = await Promise.allSettled([
          getSupplierOrders({ supplier_id: SUPPLIER_ID }),
          getForecasts({ supplier_id: SUPPLIER_ID }),
          getDeliveryPlans({ supplier_id: SUPPLIER_ID }),
          getASNList({ supplier_id: SUPPLIER_ID }),
          getStatements({ supplier_id: SUPPLIER_ID }),
          getInvoices({ supplier_id: SUPPLIER_ID }),
        ])

        const orders = ordersRes.status === 'fulfilled' && Array.isArray(ordersRes.value) ? ordersRes.value : []
        const forecasts = forecastsRes.status === 'fulfilled' && Array.isArray(forecastsRes.value) ? forecastsRes.value : []
        const plans = plansRes.status === 'fulfilled' && Array.isArray(plansRes.value) ? plansRes.value : []
        const asns = asnRes.status === 'fulfilled' && Array.isArray(asnRes.value) ? asnRes.value : []
        const statements = statementsRes.status === 'fulfilled' && Array.isArray(statementsRes.value) ? statementsRes.value : []
        const invoices = invoicesRes.status === 'fulfilled' && Array.isArray(invoicesRes.value) ? invoicesRes.value : []

        setStats({
          pendingInvitations: 1,
          pendingOrders: orders.filter((o: any) => ['pending', 'draft'].includes(o.status)).length,
          pendingDeliveryPlans: plans.filter((p: any) => !p.supplier_confirmed && p.status === 'pending').length + forecasts.filter((f: any) => !f.has_responded && f.status === 'published').length,
          pendingSettlements: statements.filter((s: any) => ['pending', 'draft'].includes(s.status)).length,
          pendingInvoices: invoices.filter((i: any) => ['pending', 'draft', 'rejected'].includes(i.status)).length + asns.filter((a: any) => a.status === 'draft').length,
        })
      } catch {
        // Keep default fallback stats.
      }
    }
    fetchStats()
  }, [])

  return (
    <div>
      <Row gutter={12} style={{ marginBottom: 20 }}>
        {quickActions.map((action) => (
          <Col span={6} key={action.path} style={{ marginBottom: 12 }}>
            <Card hoverable style={{ cursor: 'pointer', textAlign: 'center', borderRadius: 8 }}
              onClick={() => navigate(action.path)} styles={{ body: { padding: '24px 16px' } }}>
              <div style={{
                width: 48, height: 48, borderRadius: '50%',
                background: `${action.color}18`, margin: '0 auto 12px',
                display: 'flex', alignItems: 'center', justifyContent: 'center'
              }}>
                <div style={{ fontSize: 22, color: action.color }}>{action.icon}</div>
              </div>
              <div style={{ fontWeight: 600, fontSize: 14 }}>{action.label}</div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={12}>
        <Col span={16}>
          <Card title="待处理事项" style={{ borderRadius: 8 }}
            extra={<Button type="link" onClick={() => navigate('/supplier/invitations')}>查看全部 <RightOutlined /></Button>}>
            <List size="small" dataSource={todos} renderItem={(item: any) => (
              <List.Item extra={
                item.type === 'invitation'
                  ? <Button size="small" type="primary" onClick={() => navigate('/supplier/invitations')}>查看</Button>
                  : <Button size="small" onClick={() => navigate('/supplier/contracts')}>查看</Button>
              }>
                <List.Item.Meta title={<span style={{ fontSize: 13 }}>{item.text}</span>}
                  description={<Tag color="orange">{item.status === 'pending' ? '待处理' : ''}</Tag>} />
              </List.Item>
            )} />
          </Card>
        </Col>
        <Col span={8}>
          <Card style={{ borderRadius: 8, marginBottom: 12 }}>
            <Statistic title="待回复邀请" value={stats.pendingInvitations} prefix={<MessageOutlined style={{ color: '#3E5BF2' }} />} valueStyle={{ color: '#3E5BF2' }} />
          </Card>
          <Card style={{ borderRadius: 8, marginBottom: 12 }}>
            <Statistic title="待确认订单/计划" value={stats.pendingOrders + stats.pendingDeliveryPlans} prefix={<FundProjectionScreenOutlined style={{ color: '#13c2c2' }} />} valueStyle={{ color: '#13c2c2' }} />
          </Card>
          <Card style={{ borderRadius: 8 }}>
            <Statistic title="待处理财务事项" value={stats.pendingSettlements + stats.pendingInvoices} prefix={<AccountBookOutlined style={{ color: '#eb2f96' }} />} valueStyle={{ color: '#eb2f96' }} />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default SupplierHome
