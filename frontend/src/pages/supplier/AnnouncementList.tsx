import React, { useState, useEffect } from 'react'
import { List, Card, Tag, Badge, Modal, Button, Typography, Space, Empty } from 'antd'
import { 
  BellOutlined, 
  FileTextOutlined, 
  LockOutlined, 
  ReadOutlined, 
  PushpinOutlined,
  EyeOutlined 
} from '@ant-design/icons'
import { getAnnouncements, getAnnouncement, recordAnnouncementRead, getAnnouncementTypesSummary, AnnouncementItem } from '../../api'

const { Text, Title } = Typography

// 类型映射
const typeConfig: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
  announcement: { icon: <BellOutlined />, label: '公告', color: 'blue' },
  policy: { icon: <LockOutlined />, label: '政策', color: 'purple' },
  guide: { icon: <FileTextOutlined />, label: '操作指引', color: 'green' },
}

// 优先级映射
const priorityConfig: Record<number, { label: string; color: string }> = {
  0: { label: '普通', color: 'default' },
  1: { label: '重要', color: 'orange' },
  2: { label: '紧急', color: 'red' },
}

// 当前供应商ID（模拟）
const CURRENT_SUPPLIER_ID = 1

const SupplierAnnouncementList: React.FC = () => {
  const [data, setData] = useState<AnnouncementItem[]>([])
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<string>('all')
  const [detailVisible, setDetailVisible] = useState(false)
  const [selectedItem, setSelectedItem] = useState<AnnouncementItem | null>(null)
  const [typeSummary, setTypeSummary] = useState<Record<string, number>>({})

  // 加载公告列表
  const loadData = async (announcementType?: string) => {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (announcementType && announcementType !== 'all') {
        params.announcement_type = announcementType
      }
      const res = await getAnnouncements(params)
      setData(res.items)
    } catch (err) {
      console.error('加载公告失败', err)
    } finally {
      setLoading(false)
    }
  }

  // 加载类型统计
  const loadTypeSummary = async () => {
    try {
      const res = await getAnnouncementTypesSummary()
      const summary: Record<string, number> = { all: 0 }
      res.forEach((item: { type: string; count: number }) => {
        summary[item.type] = item.count
        summary.all += item.count
      })
      setTypeSummary(summary)
    } catch (err) {
      console.error('加载统计失败', err)
    }
  }

  useEffect(() => {
    loadData(activeTab === 'all' ? undefined : activeTab)
    loadTypeSummary()
  }, [activeTab])

  // 查看详情
  const handleViewDetail = async (item: AnnouncementItem) => {
    try {
      const detail = await getAnnouncement(item.id)
      setSelectedItem(detail)
      setDetailVisible(true)
      await recordAnnouncementRead(item.id, CURRENT_SUPPLIER_ID)
    } catch (err) {
      console.error('加载公告失败', err)
      setSelectedItem(item)
      setDetailVisible(true)
    }
  }

  // 渲染公告列表项
  const renderItem = (item: AnnouncementItem) => {
    const type = typeConfig[item.announcement_type] || typeConfig.announcement
    const priority = priorityConfig[item.priority] || priorityConfig[0]
    
    return (
      <List.Item
        key={item.id}
        style={{ 
          padding: '16px 24px',
          cursor: 'pointer',
          background: item.priority >= 2 ? '#fff2f0' : 'transparent',
          borderLeft: item.is_pinned ? '3px solid #fa8c16' : '3px solid transparent',
        }}
        onClick={() => handleViewDetail(item)}
      >
        <List.Item.Meta
          avatar={
            <div style={{
              width: 48,
              height: 48,
              borderRadius: 8,
              background: `${type.color}15`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 20,
              color: type.color,
            }}>
              {type.icon}
            </div>
          }
          title={
            <Space>
              <span style={{ fontWeight: item.is_pinned || item.priority >= 1 ? 600 : 400 }}>
                {item.is_pinned && <PushpinOutlined style={{ color: '#fa8c16', marginRight: 4 }} />}
                {item.title}
              </span>
              {item.priority > 0 && (
                <Tag color={priority.color} style={{ marginLeft: 8 }}>
                  {priority.label}
                </Tag>
              )}
            </Space>
          }
          description={
            <Space style={{ marginTop: 4 }}>
              <Tag color={type.color}>{type.label}</Tag>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {item.published_by} · {new Date(item.published_at).toLocaleDateString('zh-CN')}
              </Text>
              <Text type="secondary" style={{ fontSize: 12 }}>
                <EyeOutlined style={{ marginRight: 4 }} />{item.view_count}次阅读
              </Text>
            </Space>
          }
        />
      </List.Item>
    )
  }

  // Tab 配置
  const tabs = [
    { key: 'all', label: `全部 (${typeSummary.all || 0})` },
    { key: 'announcement', label: `公告 (${typeSummary.announcement || 0})` },
    { key: 'policy', label: `政策 (${typeSummary.policy || 0})` },
    { key: 'guide', label: `操作指引 (${typeSummary.guide || 0})` },
  ]

  return (
    <div style={{ padding: 24 }}>
      <Card 
        title={
          <Space>
            <ReadOutlined />
            <span>公告通知 (US-501-2)</span>
          </Space>
        }
        styles={{ body: { padding: 0 } }}
      >
        {/* 类型 Tab */}
        <div style={{ 
          display: 'flex', 
          borderBottom: '1px solid #f0f0f0',
          padding: '0 24px',
          background: '#fafafa'
        }}>
          {tabs.map((tab) => (
            <div
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: '12px 16px',
                cursor: 'pointer',
                borderBottom: activeTab === tab.key ? '2px solid #1890ff' : '2px solid transparent',
                color: activeTab === tab.key ? '#1890ff' : '#666',
                fontWeight: activeTab === tab.key ? 600 : 400,
              }}
            >
              {tab.label}
            </div>
          ))}
        </div>

        {/* 公告列表 */}
        <List
          loading={loading}
          dataSource={data}
          renderItem={renderItem}
          locale={{
            emptyText: (
              <Empty 
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无公告"
              />
            )
          }}
        />
      </Card>

      {/* 详情弹窗 */}
      <Modal
        title={null}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={
          <Button onClick={() => setDetailVisible(false)}>关闭</Button>
        }
        width={700}
        bodyStyle={{ padding: 0 }}
      >
        {selectedItem && (
          <div>
            {/* 头部信息 */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #f0f0f0' }}>
              <Space wrap style={{ marginBottom: 12 }}>
                <Tag color={typeConfig[selectedItem.announcement_type]?.color}>
                  {typeConfig[selectedItem.announcement_type]?.icon} {typeConfig[selectedItem.announcement_type]?.label}
                </Tag>
                {selectedItem.priority > 0 && (
                  <Tag color={priorityConfig[selectedItem.priority]?.color}>
                    {priorityConfig[selectedItem.priority]?.label}
                  </Tag>
                )}
                {selectedItem.is_pinned && (
                  <Tag icon={<PushpinOutlined />} color="orange">置顶</Tag>
                )}
              </Space>
              <Title level={4} style={{ marginBottom: 8 }}>{selectedItem.title}</Title>
              <Text type="secondary">
                {selectedItem.published_by} 发布于 {new Date(selectedItem.published_at).toLocaleString('zh-CN')}
                <span style={{ marginLeft: 16 }}>
                  <EyeOutlined /> {selectedItem.view_count} 次阅读
                </span>
              </Text>
            </div>
            
            {/* 正文内容 */}
            <div style={{ padding: '24px' }}>
              <div style={{ 
                whiteSpace: 'pre-wrap', 
                lineHeight: 1.8,
                fontSize: 14,
              }}>
                {selectedItem.content}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default SupplierAnnouncementList
