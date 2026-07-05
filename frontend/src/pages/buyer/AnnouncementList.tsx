import React, { useState, useEffect } from 'react'
import { Table, Card, Button, Modal, Form, Input, Select, Tag, Space, message, Popconfirm, Tabs, Badge } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, EyeOutlined, PushpinOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import { getAnnouncements, createAnnouncement, updateAnnouncement, deleteAnnouncement, getAnnouncementTypesSummary, AnnouncementItem } from '../../api'

const { TextArea } = Input

// 类型标签映射
const typeLabels: Record<string, { label: string; color: string }> = {
  announcement: { label: '公告', color: 'blue' },
  policy: { label: '政策', color: 'purple' },
  guide: { label: '操作指引', color: 'green' },
}

// 优先级标签
const priorityLabels: Record<number, { label: string; color: string }> = {
  0: { label: '普通', color: 'default' },
  1: { label: '重要', color: 'orange' },
  2: { label: '紧急', color: 'red' },
}

const BuyerAnnouncementList: React.FC = () => {
  const [data, setData] = useState<AnnouncementItem[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [detailVisible, setDetailVisible] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [selectedItem, setSelectedItem] = useState<AnnouncementItem | null>(null)
  const [typeSummary, setTypeSummary] = useState<Record<string, number>>({})
  const [activeTab, setActiveTab] = useState<string>('all')
  const [form] = Form.useForm()

  // 加载数据
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
      message.error('加载公告列表失败')
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

  // 打开新增/编辑弹窗
  const openModal = (record?: AnnouncementItem) => {
    if (record) {
      setEditingId(record.id)
      form.setFieldsValue({
        ...record,
        is_pinned: record.is_pinned,
      })
    } else {
      setEditingId(null)
      form.resetFields()
      form.setFieldsValue({
        announcement_type: 'announcement',
        priority: 0,
        is_pinned: false,
        published_by: '张明远',
      })
    }
    setModalVisible(true)
  }

  // 提交表单
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingId) {
        await updateAnnouncement(editingId, values)
        message.success('公告更新成功')
      } else {
        await createAnnouncement(values)
        message.success('公告发布成功')
      }
      setModalVisible(false)
      loadData(activeTab === 'all' ? undefined : activeTab)
      loadTypeSummary()
    } catch (err: any) {
      message.error(err.message || '操作失败')
    }
  }

  // 删除公告
  const handleDelete = async (id: number) => {
    try {
      await deleteAnnouncement(id)
      message.success('公告已删除')
      loadData(activeTab === 'all' ? undefined : activeTab)
      loadTypeSummary()
    } catch (err) {
      message.error('删除失败')
    }
  }

  // 查看详情
  const viewDetail = async (record: AnnouncementItem) => {
    setSelectedItem(record)
    setDetailVisible(true)
  }

  // 表格列定义
  const columns: ColumnsType<AnnouncementItem> = [
    {
      title: '类型',
      dataIndex: 'announcement_type',
      key: 'announcement_type',
      width: 100,
      render: (type: string) => (
        <Tag color={typeLabels[type]?.color}>{typeLabels[type]?.label || type}</Tag>
      ),
    },
    {
      title: '标题',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record) => (
        <Space>
          {record.is_pinned && <PushpinOutlined style={{ color: '#fa8c16' }} />}
          <span style={{ color: record.priority >= 2 ? '#cf1322' : 'inherit' }}>{text}</span>
          {record.priority > 0 && (
            <Tag color={priorityLabels[record.priority]?.color}>
              {priorityLabels[record.priority]?.label}
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '发布人',
      dataIndex: 'published_by',
      key: 'published_by',
      width: 100,
    },
    {
      title: '发布时间',
      dataIndex: 'published_at',
      key: 'published_at',
      width: 180,
      render: (text: string) => new Date(text).toLocaleString('zh-CN'),
    },
    {
      title: '阅读量',
      dataIndex: 'view_count',
      key: 'view_count',
      width: 80,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => viewDetail(record)}>
            查看
          </Button>
          <Button type="link" icon={<EditOutlined />} onClick={() => openModal(record)}>
            编辑
          </Button>
          <Popconfirm title="确定删除此公告？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // Tab 配置
  const tabItems = [
    { key: 'all', label: <Badge count={typeSummary.all || 0} size="small">全部</Badge> },
    { key: 'announcement', label: <Badge count={typeSummary.announcement || 0} size="small" offset={[8, 0]}>公告</Badge> },
    { key: 'policy', label: <Badge count={typeSummary.policy || 0} size="small" offset={[8, 0]}>政策</Badge> },
    { key: 'guide', label: <Badge count={typeSummary.guide || 0} size="small" offset={[8, 0]}>操作指引</Badge> },
  ]

  return (
    <Card
      title="公告管理 (US-501-1)"
      extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => openModal()}>
          发布公告
        </Button>
      }
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} style={{ marginBottom: 16 }} />

      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      {/* 新增/编辑弹窗 */}
      <Modal
        title={editingId ? '编辑公告' : '发布公告'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={700}
        okText="发布"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 20 }}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input placeholder="请输入公告标题" />
          </Form.Item>

          <Form.Item name="announcement_type" label="类型" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="announcement">公告</Select.Option>
              <Select.Option value="policy">政策</Select.Option>
              <Select.Option value="guide">操作指引</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="priority" label="优先级">
            <Select>
              <Select.Option value={0}>普通</Select.Option>
              <Select.Option value={1}>重要</Select.Option>
              <Select.Option value={2}>紧急</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="is_pinned" label="置顶" valuePropName="checked">
            <Select>
              <Select.Option value={false}>否</Select.Option>
              <Select.Option value={true}>是</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="published_by" label="发布人">
            <Input />
          </Form.Item>

          <Form.Item name="content" label="内容" rules={[{ required: true, message: '请输入内容' }]}>
            <TextArea rows={8} placeholder="请输入公告内容，支持多行文本" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情弹窗 */}
      <Modal
        title="公告详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={
          <Button onClick={() => setDetailVisible(false)}>关闭</Button>
        }
        width={700}
      >
        {selectedItem && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Tag color={typeLabels[selectedItem.announcement_type]?.color}>
                  {typeLabels[selectedItem.announcement_type]?.label}
                </Tag>
                {selectedItem.priority > 0 && (
                  <Tag color={priorityLabels[selectedItem.priority]?.color}>
                    {priorityLabels[selectedItem.priority]?.label}
                  </Tag>
                )}
                {selectedItem.is_pinned && (
                  <Tag icon={<PushpinOutlined />} color="orange">置顶</Tag>
                )}
              </Space>
            </div>
            <h2 style={{ marginBottom: 16 }}>{selectedItem.title}</h2>
            <div style={{ marginBottom: 16, color: '#666' }}>
              发布人：{selectedItem.published_by} | 发布时间：{new Date(selectedItem.published_at).toLocaleString('zh-CN')} | 阅读量：{selectedItem.view_count}
            </div>
            <div style={{ 
              whiteSpace: 'pre-wrap', 
              lineHeight: 1.8,
              background: '#f5f5f5',
              padding: 16,
              borderRadius: 8
            }}>
              {selectedItem.content}
            </div>
          </div>
        )}
      </Modal>
    </Card>
  )
}

export default BuyerAnnouncementList
