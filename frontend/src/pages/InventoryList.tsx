import React, { useEffect, useState } from 'react'
import { Table, Card, Input, Select, Button, Space, Tag, Row, Col, Statistic } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { getInventory, getInventoryStats } from '../api'

const InventoryList: React.FC = () => {
  const [inventory, setInventory] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('原料库存')
  const [stats, setStats] = useState<any>(null)
  const [searchKeyword, setSearchKeyword] = useState('')

  useEffect(() => { loadData() }, [])
  const loadData = async () => {
    setLoading(true)
    try {
      const results = await Promise.allSettled([getInventory({ page: 1, page_size: 20 }), getInventoryStats()])
      const i = results[0].status === 'fulfilled' ? results[0].value : []
      const s = results[1].status === 'fulfilled' ? results[1].value : null
      const data = Array.isArray(i) ? i : []
      setInventory(data); setTotal(data.length); setStats(s)
    } finally { setLoading(false) }
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    '正常': { color: 'green', text: '正常' }, '预警': { color: 'orange', text: '预警' },
    '不足': { color: 'red', text: '不足' }, '超储': { color: 'purple', text: '超储' }
  }

  const columns = [
    { title: '物料名称', dataIndex: 'name', key: 'name' },
    { title: '分类', dataIndex: 'category', key: 'category', width: 100 },
    { title: '库存数量', dataIndex: 'stock_quantity', key: 'stock_quantity', width: 100, render: (v: number, r: any) => `${v} ${r.unit}` },
    { title: '单价', dataIndex: 'unit_price', key: 'unit_price', width: 100, render: (v: number) => v ? `¥${v.toLocaleString()}` : '-' },
    { title: '安全库存点', dataIndex: 'reorder_point', key: 'reorder_point', width: 100 },
    { title: '产地', dataIndex: 'origin', key: 'origin', width: 120 },
    { title: '状态', key: 'status', width: 80, render: (_: any, r: any) => {
      const qty = r.stock_quantity || 0
      const reorder = r.reorder_point || 0
      const status = qty <= reorder * 0.5 ? '不足' : qty <= reorder ? '预警' : '正常'
      return <Tag color={statusMap[status]?.color}>{statusMap[status]?.text || status}</Tag>
    }}
  ]

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 16 }}>库存查询</h2>
      <Card bordered={false} size="small" style={{ marginBottom: 16 }}>
        <Space><Button type={tab === '原料库存' ? 'primary' : 'default'} onClick={() => setTab('原料库存')}>原料库存</Button><Button type={tab === '成品库存' ? 'primary' : 'default'} onClick={() => setTab('成品库存')}>成品库存</Button></Space>
      </Card>
      <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
        <Col span={6}><Card bordered={false} size="small"><Statistic title="库存总量" value={stats?.total_quantity || 0} suffix="吨" loading={loading} /></Card></Col>
        <Col span={6}><Card bordered={false} size="small"><Statistic title="库存价值" value={stats?.total_value || 0} prefix="¥" loading={loading} /></Card></Col>
        <Col span={6}><Card bordered={false} size="small"><Statistic title="正常" value={stats?.normal_count || 0} valueStyle={{ color: '#52C41A' }} /></Card></Col>
        <Col span={6}><Card bordered={false} size="small"><Statistic title="预警" value={stats?.warning_count || 0} valueStyle={{ color: '#FAAD14' }} /></Card></Col>
      </Row>
      <Card bordered={false} size="small" style={{ marginBottom: 16 }}>
        <Space><Input placeholder="搜索物料名称" prefix={<SearchOutlined />} style={{ width: 160 }} value={searchKeyword} onChange={(e) => setSearchKeyword(e.target.value)} /><Button type="primary" onClick={() => {}}>查询</Button><Button onClick={() => setSearchKeyword('')}>重置</Button></Space>
      </Card>
      <Card bordered={false} size="small">
        <Table columns={columns} dataSource={inventory.filter(item => !searchKeyword || item.name?.toLowerCase().includes(searchKeyword.toLowerCase()) || item.category?.toLowerCase().includes(searchKeyword.toLowerCase()))} rowKey="id" loading={loading} pagination={{ total, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }} />
      </Card>
    </div>
  )
}
export default InventoryList
