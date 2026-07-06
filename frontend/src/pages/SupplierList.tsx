import React, { useEffect, useState } from 'react'
import { Table, Card, Input, Select, Button, Space, Tag, Rate, Row, Col, Statistic } from 'antd'
import { SearchOutlined, PlusOutlined, EditOutlined, EyeOutlined } from '@ant-design/icons'
import { getSuppliers, getSupplierStats } from '../api'

const SupplierList: React.FC = () => {
  const [suppliers, setSuppliers] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<any>(null)
  const [searchKeyword, setSearchKeyword] = useState('')

  useEffect(() => { loadData() }, [])
  const loadData = async () => {
    setLoading(true)
    try {
      const results = await Promise.allSettled([getSuppliers({ page: 1, page_size: 20 }), getSupplierStats()])
      const s = results[0].status === 'fulfilled' ? results[0].value : []
      const st = results[1].status === 'fulfilled' ? results[1].value : null
      const data = Array.isArray(s) ? s : []
      setSuppliers(data); setTotal(data.length); setStats(st)
    } finally { setLoading(false) }
  }

  const statusMap: Record<string, { color: string; text: string }> = {
    '合作中': { color: 'green', text: '合作中' }, '待审核': { color: 'orange', text: '待审核' },
    '暂停': { color: 'red', text: '暂停' }
  }
  const levelMap: Record<string, number> = { A: 5, B: 3, C: 1 }

  const columns = [
    { title: '供应商名称', dataIndex: 'name', key: 'name', width: 200 },
    { title: '联系人', dataIndex: 'contact_person', key: 'contact_person', width: 100 },
    { title: '联系电话', dataIndex: 'phone', key: 'phone', width: 130 },
    { title: '邮箱', dataIndex: 'email', key: 'email', width: 180 },
    { title: '地址', dataIndex: 'address', key: 'address', width: 200 },
    { title: '评级', dataIndex: 'rating', key: 'rating', width: 80, render: (v: number) => <Rate disabled defaultValue={v || 0} style={{ fontSize: 12 }} allowHalf /> },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: (v: string) => <Tag color={statusMap[v]?.color}>{statusMap[v]?.text || v}</Tag> },
    { title: '操作', key: 'action', width: 120, render: () => <Space><Button type="link" size="small" icon={<EyeOutlined />}>查看</Button><Button type="link" size="small" icon={<EditOutlined />}>编辑</Button></Space> }
  ]

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 16 }}>供应商列表</h2>
      <Row gutter={[8, 8]} style={{ marginBottom: 16 }}>
        <Col span={6}><Card bordered={false} size="small"><Statistic title="供应商总数" value={stats?.total || 0} loading={loading} /></Card></Col>
        <Col span={6}><Card bordered={false} size="small"><Statistic title="合作中" value={stats?.active || 0} valueStyle={{ color: '#52C41A' }} /></Card></Col>
        <Col span={6}><Card bordered={false} size="small"><Statistic title="待审核" value={stats?.pending || 0} valueStyle={{ color: '#FAAD14' }} /></Card></Col>
        <Col span={6}><Card bordered={false} size="small"><Statistic title="已暂停" value={stats?.suspended || 0} valueStyle={{ color: '#FF4D4F' }} /></Card></Col>
      </Row>
      <Card bordered={false} size="small" style={{ marginBottom: 16 }}>
        <Space><Input placeholder="搜索供应商名称" prefix={<SearchOutlined />} style={{ width: 160 }} value={searchKeyword} onChange={(e) => setSearchKeyword(e.target.value)} /><Button type="primary" onClick={() => {}}>查询</Button><Button onClick={() => setSearchKeyword('')}>重置</Button><Button type="primary" icon={<PlusOutlined />}>新增供应商</Button></Space>
      </Card>
      <Card bordered={false} size="small">
        <Table columns={columns} dataSource={suppliers.filter(item => !searchKeyword || item.name?.toLowerCase().includes(searchKeyword.toLowerCase()) || item.contact_person?.toLowerCase().includes(searchKeyword.toLowerCase()))} rowKey="id" loading={loading} pagination={{ total, showSizeChanger: true, showTotal: (t: number) => `共 ${t} 条` }} />
      </Card>
    </div>
  )
}
export default SupplierList
