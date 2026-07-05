import React, { useEffect, useState } from 'react'
import { Table, Tag, Button, Modal, Form, Input, Select, Card, message, Descriptions, Alert } from 'antd'
import { PlusOutlined, EyeOutlined, FileSearchOutlined } from '@ant-design/icons'
import {
  getQualificationProjects, createQualificationProject, getQualificationProject,
  getQualificationSubmissions, getQualificationSubmission,
} from '../../api'
import { getSuppliers } from '../../api'

const statusMap: Record<string, { color: string; text: string }> = {
  pending_response: { color: 'blue', text: '待响应' },
  in_progress: { color: 'orange', text: '评审中' },
  supplement_materials: { color: 'gold', text: '待补充材料' },
  approved: { color: 'green', text: '已通过' },
  rejected: { color: 'red', text: '已驳回' },
}

const answerLabels: Record<string, string> = {
  company_scale: '企业规模',
  registered_capital: '注册资本(万元)',
  annual_revenue: '年营业额(万元)',
  main_markets: '主要市场区域',
  production_capacity: '年产能(吨)',
  production_lines: '生产线数量',
  warehouse_capacity: '仓储能力(吨)',
  lead_time_days: '常规交期(天)',
  has_iso9001: 'ISO9001认证',
  has_iso22000: 'ISO22000认证',
  has_haccp: 'HACCP认证',
  quality_score_self: '自评质量得分',
  quality_cert_files: '质量证书',
  latest_revenue: '最近一年营业额(万元)',
  latest_profit: '最近一年净利润(万元)',
  current_assets: '流动资产(万元)',
  current_liabilities: '流动负债(万元)',
  has_tax_cert: '完税证明',
  major_clients: '主要客户',
  has_baijiu_exp: '白酒行业经验',
  cooperation_files: '合作证明材料',
}

const QualificationProjectList: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()
  const [suppliers, setSuppliers] = useState<any[]>([])
  const [detailOpen, setDetailOpen] = useState(false)
  const [detail, setDetail] = useState<any>(null)
  const [submissions, setSubmissions] = useState<any[]>([])
  const [submissionOpen, setSubmissionOpen] = useState(false)
  const [submissionDetail, setSubmissionDetail] = useState<any>(null)

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await getQualificationProjects() as any
      setData(Array.isArray(res) ? res : [])
    } catch { setData([]) }
    setLoading(false)
  }

  const fetchSuppliers = async () => {
    try {
      const res = await getSuppliers() as any
      setSuppliers(Array.isArray(res) ? res : [])
    } catch { /* ignore */ }
  }

  useEffect(() => { fetchData(); fetchSuppliers() }, [])

  const handleCreate = async () => {
    try {
      const values = await form.validateFields()
      const res = await createQualificationProject({
        project_name: values.project_name,
        target_categories: values.target_categories || '原料',
        target_supplier_ids: values.target_supplier_ids || [],
        notes: values.notes,
        deadline: values.deadline,
      }) as any
      message.success(`评审项目已创建，已邀请 ${res?.invited_suppliers?.length ?? 0} 家供应商`)
      setModalOpen(false)
      form.resetFields()
      fetchData()
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('创建失败')
    }
  }

  const showDetail = async (id: number) => {
    try {
      const res = await getQualificationProject(id) as any
      setDetail(res)
      const subs = await getQualificationSubmissions(id) as any
      setSubmissions(Array.isArray(subs) ? subs : [])
      setDetailOpen(true)
    } catch { message.error('获取详情失败') }
  }

  const showSubmission = async (projectId: number, supplierId: number) => {
    try {
      const res = await getQualificationSubmission(projectId, supplierId) as any
      setSubmissionDetail(res)
      setSubmissionOpen(true)
    } catch { message.error('获取提交详情失败') }
  }

  const columns = [
    { title: '项目名称', dataIndex: 'project_name', key: 'project_name' },
    { title: '评审品类', dataIndex: 'target_categories', key: 'target_categories', ellipsis: true },
    { title: '状态', dataIndex: 'status', key: 'status', render: (v: string) => {
      const s = statusMap[v] || { color: 'default', text: v }
      return <Tag color={s.color}>{s.text}</Tag>
    }},
    { title: '邀请/已响应', key: 'counts', render: (_: any, r: any) => `${r.invited_count || 0} / ${r.accepted_count || 0}` },
    { title: '截止日期', dataIndex: 'deadline', key: 'deadline', render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      <Button type="link" icon={<EyeOutlined />} size="small" onClick={() => showDetail(r.id)}>查看</Button>
    )},
  ]

  return (
    <div>
      <Card title="资格评审项目 (US-104-1 / US-105-2)" extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>创建评审项目</Button>
      }>
        <Table rowKey="id" dataSource={data} columns={columns} loading={loading} pagination={{ pageSize: 10 }} />
      </Card>

      <Modal title="创建资格评审项目 (US-104-1)" open={modalOpen} onOk={handleCreate} onCancel={() => { setModalOpen(false); form.resetFields() }} width={560}>
        <Form form={form} layout="vertical">
          <Form.Item name="project_name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="如：2026年度高粱供应商资格评审" />
          </Form.Item>
          <Form.Item name="target_categories" label="评审品类" rules={[{ required: true, message: '请输入评审品类' }]}>
            <Input placeholder="如：高粱、小麦等原料" />
          </Form.Item>
          <Form.Item name="notes" label="评审要求说明">
            <Input.TextArea rows={2} placeholder="发布给供应商的评审要求" />
          </Form.Item>
          <Form.Item name="target_supplier_ids" label="目标供应商" rules={[{ required: true, message: '请选择目标供应商' }]}>
            <Select mode="multiple" placeholder="选择供应商" optionFilterProp="label">
              {suppliers.map((s: any) => (
                <Select.Option key={s.id} value={s.id} label={s.name}>{s.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="deadline" label="截止日期">
            <Input type="date" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="评审项目详情" open={detailOpen} onCancel={() => setDetailOpen(false)} footer={null} width={760}>
        {detail && (
          <>
            <Descriptions bordered column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="项目名称" span={2}>{detail.project_name}</Descriptions.Item>
              <Descriptions.Item label="评审品类">{detail.target_categories || '-'}</Descriptions.Item>
              <Descriptions.Item label="状态"><Tag color={statusMap[detail.status]?.color}>{statusMap[detail.status]?.text || detail.status}</Tag></Descriptions.Item>
              <Descriptions.Item label="截止日期">{detail.deadline ? new Date(detail.deadline).toLocaleDateString() : '-'}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{detail.created_at ? new Date(detail.created_at).toLocaleString() : '-'}</Descriptions.Item>
              {detail.notes && <Descriptions.Item label="评审要求" span={2}>{detail.notes}</Descriptions.Item>}
            </Descriptions>
            <h4>供应商提交记录 (US-105-2)</h4>
            <Table rowKey="submission_id" dataSource={submissions} columns={[
              { title: '供应商', dataIndex: 'supplier_name', key: 'supplier_name' },
              { title: '提交状态', dataIndex: 'status', key: 'status', render: (v: string) => {
                const s = statusMap[v] || { color: 'default', text: v }
                return <Tag color={s.color}>{s.text}</Tag>
              }},
              { title: '已填问卷', dataIndex: 'has_answers', key: 'has_answers', render: (v: boolean) => v ? <Tag color="green">是</Tag> : <Tag>否</Tag> },
              { title: '提交时间', dataIndex: 'submitted_at', key: 'submitted_at', render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
              { title: '操作', key: 'action', render: (_: any, r: any) => (
                r.has_answers ? (
                  <Button type="link" size="small" icon={<FileSearchOutlined />} onClick={() => showSubmission(detail.id, r.supplier_id)}>
                    查看问卷
                  </Button>
                ) : null
              )},
            ]} size="small" pagination={false} />
          </>
        )}
      </Modal>

      <Modal title="供应商问卷详情 (US-105-2)" open={submissionOpen} onCancel={() => setSubmissionOpen(false)} footer={null} width={640}>
        {submissionDetail && (
          <>
            <Descriptions bordered column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="供应商">{submissionDetail.supplier_name}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={statusMap[submissionDetail.status]?.color}>{statusMap[submissionDetail.status]?.text || submissionDetail.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="更新时间" span={2}>
                {submissionDetail.updated_at ? new Date(submissionDetail.updated_at).toLocaleString() : '-'}
              </Descriptions.Item>
            </Descriptions>
            <Descriptions bordered column={1} size="small" title="问卷答案">
              {Object.entries(submissionDetail.answers || {}).map(([key, value]) => (
                <Descriptions.Item key={key} label={answerLabels[key] || key}>
                  {String(value ?? '-')}
                </Descriptions.Item>
              ))}
            </Descriptions>
          </>
        )}
      </Modal>
    </div>
  )
}

export default QualificationProjectList
