import React, { useEffect, useState } from 'react'
import { Card, Table, Tag, Descriptions, Modal, Button, Space, Statistic, Row, Col, Upload, message, Typography } from 'antd'
import { EyeOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons'
import { getForecasts, importForecastExcel } from '../../api'

const ForecastList: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [detailOpen, setDetailOpen] = useState(false)
  const [detail, setDetail] = useState<any>(null)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<any>(null)
  const [resultOpen, setResultOpen] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await getForecasts()
      const rows = (res as any)?.data ?? res
      setData(Array.isArray(rows) ? rows : [])
    } catch { setData([]) }
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const statusMap: Record<string, { color: string; text: string }> = {
    draft: { color: 'default', text: '草稿' },
    published: { color: 'blue', text: '已发布' },
    confirmed: { color: 'green', text: '已确认' },
    partial: { color: 'orange', text: '部分响应' },
    expired: { color: 'red', text: '已过期' },
  }

  const handleImport = async (file: File) => {
    setImporting(true)
    try {
      const result: any = await importForecastExcel(file)
      setImportResult(result)
      setResultOpen(true)
      message.success(result.message || '导入成功')
      fetchData() // 刷新列表
    } catch (e: any) {
      const errMsg = e?.response?.data?.detail || e?.message || '导入失败'
      message.error(errMsg)
    } finally {
      setImporting(false)
    }
    return false // 阻止自动上传
  }

  // 生成 Excel 模板
  const downloadTemplate = () => {
    const BOM = '\uFEFF'
    const headers = ['物料名称', '物料ID', '预测月份', '预测数量(吨)', '备注']
    const sampleData = [
      ['高粱', '1', '2026-08', '500', '酿酒用'],
      ['小麦', '2', '2026-08', '300', '制曲用'],
      ['大米', '3', '2026-08', '200', ''],
      ['玉米', '4', '2026-08', '150', '辅料'],
    ]
    const csvContent = [headers.join(','), ...sampleData.map(r => r.join(','))].join('\n')
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 采购预测导入模板_.csv
    a.click()
    URL.revokeObjectURL(url)
  }

  const columns = [
    { title: '预测期间', dataIndex: 'forecast_period', key: 'forecast_period', render: (v: string) => v || '-' },
    {
      title: '供应商', key: 'supplier',
      render: (_: unknown, r: any) => r.supplier_name || 供应商#,
    },
    {
      title: '物料/品类', key: 'items', render: (_: unknown, r: any) => {
        const items = r.items_data
        if (typeof items === 'string') {
          try {
            const parsed = JSON.parse(items)
            if (Array.isArray(parsed) && parsed[0]?.material_name) return parsed[0].material_name
          } catch { return '—' }
        }
        if (Array.isArray(items) && items[0]?.material_name) return items[0].material_name
        return '—'
      }
    },
    {
      title: '预测数量', key: 'qty', render: (_: unknown, r: any) => {
        let items = r.items_data
        if (typeof items === 'string') {
          try { items = JSON.parse(items) } catch { return '—' }
        }
        if (!Array.isArray(items) || !items.length) return '—'
        const q = items.reduce((s: number, x: any) => s + (Number(x.quantity) || 0), 0)
        return q ? ${q} 吨 : '—'
      }
    },
    {
      title: '周期起止', key: 'period', render: (_: unknown, r: any) => (
        <span>{r.period_start ? new Date(r.period_start).toLocaleDateString() : '—'} ~ {r.period_end ? new Date(r.period_end).toLocaleDateString() : '—'}</span>
      )
    },
    {
      title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => {
        const s = statusMap[v] || { color: 'blue', text: v || '已发布' }
        return <Tag color={s.color}>{s.text}</Tag>
      }
    },
    { title: '来源', key: 'source', render: () => <Tag color="purple">ERP同步/Excel导入</Tag> },
    {
      title: '操作', key: 'action', render: (_: any, r: any) => (
        <Button type="link" icon={<EyeOutlined />} size="small" onClick={() => { setDetail(r); setDetailOpen(true) }}>查看</Button>
      )
    },
  ]

  return (
    <div>
      <Card
        title="采购预测 (US-301)"
        extra={
          <Space>
            <Button icon={<DownloadOutlined />} onClick={downloadTemplate}>下载模板</Button>
            <Upload
              accept=".xlsx,.xls,.csv"
              showUploadList={false}
              beforeUpload={handleImport}
              disabled={importing}
            >
              <Button type="primary" icon={<UploadOutlined />} loading={importing}>
                {importing ? '导入中...' : 'Excel导入'}
              </Button>
            </Upload>
          </Space>
        }
      >
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}><Statistic title="预测总数" value={data.length} /></Col>
          <Col span={6}><Statistic title="已响应" value={data.filter((d: any) => d.status === 'confirmed' || d.status === 'partial').length} /></Col>
          <Col span={6}><Statistic title="待响应" value={data.filter((d: any) => d.status === 'draft' || d.status === 'published').length} /></Col>
        </Row>
        <Table rowKey="id" dataSource={data} columns={columns} loading={loading} pagination={{ pageSize: 10 }} />
      </Card>

      <Modal title="预测详情" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={600}>
        {detail && (
          <Descriptions bordered column={2} size="small">
            <Descriptions.Item label="预测期间">{detail.forecast_period || '-'}</Descriptions.Item>
            <Descriptions.Item label="状态"><Tag color="blue">{detail.status || '—'}</Tag></Descriptions.Item>
            <Descriptions.Item label="供应商">{detail.supplier_name || 供应商#}</Descriptions.Item>
            <Descriptions.Item label="周期">{detail.period_start ? new Date(detail.period_start).toLocaleDateString() : '—'} ~ {detail.period_end ? new Date(detail.period_end).toLocaleDateString() : '—'}</Descriptions.Item>
            <Descriptions.Item label="明细" span={2}>
              <pre style={{ margin: 0, fontSize: 12, maxHeight: 300, overflow: 'auto' }}>
                {(() => {
                  let items = detail.items_data
                  if (typeof items === 'string') {
                    try { items = JSON.parse(items) } catch { return items }
                  }
                  return JSON.stringify(items, null, 2)
                })()}
              </pre>
            </Descriptions.Item>
            <Descriptions.Item label="数据来源"><Tag color="purple">协同发布</Tag></Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      <Modal
        title="导入结果"
        open={resultOpen}
        onCancel={() => setResultOpen(false)}
        footer={<Button type="primary" onClick={() => setResultOpen(false)}>确定</Button>}
      >
        {importResult && (
          <div>
            <p style={{ fontSize: 16, color: '#52c41a' }}>✅ {importResult.message}</p>
            <p>明细条数：<strong>{importResult.items_count}</strong></p>
            <p>分发给供应商数：<strong>{importResult.suppliers_count}</strong></p>
            {importResult.errors && importResult.errors.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <Typography.Text type="warning">警告（已跳过）：</Typography.Text>
                {importResult.errors.map((e: string, i: number) => (
                  <p key={i} style={{ fontSize: 12, color: '#faad14', margin: 0 }}>{e}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default ForecastList



