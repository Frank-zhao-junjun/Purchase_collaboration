import React, { useEffect, useState } from 'react'
import { Table, Card, Input, Select, Button, Space, Tag, Row, Col, Statistic } from 'antd'
import { SearchOutlined, PlusOutlined, EyeOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { getOrders, getOrderStats } from '../api'

const PurchaseOrderList: React.FC = () => {
  const navigate = useNavigate()
  const [orders, setOrders] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [stats, setStats] = useState<any>(null)
  const [searchKeyword, setSearchKeyword] = useState('')

  useEffect(() => { loadOrders() }, [page])
  useEffect(() => { getOrderStats().then(setStats) }, [])

  const loadOrders = async () => {
    setLoading(true)
    try {
      const res: any = await getOrders({ page, page_size: 20 })
      const data = Array.isArray(res) ? res : []
      setOrders(data); setTotal(data.length)
    } finally { setLoading(false) }
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    '草稿': { color: 'default', text: '草稿' }, '已提交': { color: 'orange', text: '已提交' },
    '已确认': { color: 'blue', text: '已确认' }, '已发货': { color: 'cyan', text: '已发货' },
    '已到货': { color: 'purple', text: '已到货' }, '已入库': { color: 'green', text: '已入库' }
  }

  const columns = [
    { title: '订单编号', dataIndex: 'order_no', key: 'order_no', width: 180 },
    { title: '计划类型', dataIndex: 'plan_type', key: 'plan_type', width: 100 },
    { title: '订单金额', dataIndex: 'total_amount', key: 'total_amount', width: 120, render: (v: number) => `¥${v?.toLocaleString() || 0}` },
    { title: '预计交货日期', dataIndex: 'expected_delivery_date', key: 'expected_delivery_date', width: 120 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text || v}</Tag> },
    { title: '创建人', dataIndex: 'created_by', key: 'created_by', width: 100 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 160 },
    { title: '操作', key: 'action', width: 100, render: (_: any, r: any) => <Button type="link" icon={<EyeOutlined />} onClick={() => navigate(`/orders/${r.id}`)}>查看</Button> }
  ]

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 16 }}>采购订单列表</h2>
      <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
        <Col span={4}><Card bordered={false} size="small"><Statistic title="订单总数" value={stats?.total || 0} loading={loading} /></Card></Col>
        <Col span={4}><Card bordered={false} size="small"><Statistic title="已提交" value={stats?.pending || 0} valueStyle={{ color: '#FAAD14' }} /></Card></Col>
        <Col span={4}><Card bordered={false} size="small"><Statistic title="已确认" value={stats?.confirmed || 0} valueStyle={{ color: '#3E5BF2' }} /></Card></Col>
        <Col span={4}><Card bordered={false} size="small"><Statistic title="已发货" value={stats?.shipped || 0} valueStyle={{ color: '#1890FF' }} /></Card></Col>
        <Col span={4}><Card bordered={false} size="small"><Statistic title="已到货" value={stats?.delivered || 0} valueStyle={{ color: '#52C41A' }} /></Card></Col>
        <Col span={4}><Card bordered={false} size="small"><Statistic title="总金额" value={stats?.total_amount || 0} prefix="¥" loading={loading} /></Card></Col>
      </Row>
      <Card bordered={false} size="small" style={{ marginBottom: 16 }}>
        <Space><Input placeholder="搜索订单编号" prefix={<SearchOutlined />} style={{ width: 160 }} value={searchKeyword} onChange={(e) => setSearchKeyword(e.target.value)} /><Button type="primary" onClick={() => {}}>查询</Button><Button onClick={() => setSearchKeyword('')}>重置</Button><Button type="primary" icon={<PlusOutlined />}>新建订单</Button></Space>
      </Card>
      <Card bordered={false} size="small">
        <Table columns={columns} dataSource={orders.filter(item => !searchKeyword || item.order_no?.toLowerCase().includes(searchKeyword.toLowerCase()))} rowKey="id" loading={loading} pagination={{ current: page, pageSize: 20, total, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条`, onChange: (p) => setPage(p) }} />
      </Card>
    </div>
  )
}
export default PurchaseOrderList
