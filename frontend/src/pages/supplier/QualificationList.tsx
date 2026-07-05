import React, { useEffect, useState } from 'react'
import { Table, Tag, Button, Modal, Form, Input, Select, Card, Space, message, Descriptions, Collapse, InputNumber } from 'antd'
import { FileTextOutlined, UploadOutlined, EyeOutlined } from '@ant-design/icons'
import { getQualificationProjects, getQualificationProject, getQuestionnaire, submitQualification } from '../../api'

const SUPPLIER_ID = 1

const projectStatusMap: Record<string, { color: string; text: string }> = {
  pending_response: { color: 'blue', text: '待响应' },
  in_progress: { color: 'orange', text: '评审中' },
  supplement_materials: { color: 'gold', text: '待补充材料' },
  approved: { color: 'green', text: '已通过' },
  rejected: { color: 'red', text: '已驳回' },
}

const SupplierQualification: React.FC = () => {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [fillOpen, setFillOpen] = useState(false)
  const [viewOpen, setViewOpen] = useState(false)
  const [currentProject, setCurrentProject] = useState<any>(null)
  const [viewDetail, setViewDetail] = useState<any>(null)
  const [questionnaire, setQuestionnaire] = useState<any>(null)
  const [form] = Form.useForm()

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await getQualificationProjects({ supplier_id: SUPPLIER_ID }) as any
      setData(Array.isArray(res) ? res : [])
    } catch { setData([]) }
    setLoading(false)
  }

  useEffect(() => { fetchData() }, [])

  const handleView = async (project: any) => {
    try {
      const detail = await getQualificationProject(project.id) as any
      setViewDetail(detail)
      setViewOpen(true)
    } catch { message.error('获取项目详情失败') }
  }

  const handleFill = async (project: any) => {
    setCurrentProject(project)
    try {
      const q = await getQuestionnaire(project.id, { params: { supplier_id: SUPPLIER_ID } }) as any
      setQuestionnaire(q)
      const initialValues: Record<string, string> = {}
      if (q?.sections && Array.isArray(q.sections)) {
        q.sections.forEach((section: any) => {
          if (section.fields && Array.isArray(section.fields)) {
            section.fields.forEach((field: any) => {
              initialValues[field.id] = ''
            })
          }
        })
      }
      form.setFieldsValue(initialValues)
      setFillOpen(true)
    } catch {
      setQuestionnaire(null)
      setFillOpen(true)
    }
  }

  const handleSubmit = async () => {
    if (!currentProject) return
    try {
      const values = await form.validateFields()
      await submitQualification(currentProject.id, {
        supplier_id: SUPPLIER_ID,
        answers: values,
      })
      message.success('问卷已提交')
      setFillOpen(false)
      form.resetFields()
      fetchData()
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('提交失败')
    }
  }

  const columns = [
    { title: '项目名称', dataIndex: 'project_name', key: 'project_name' },
    { title: '品类范围', dataIndex: 'target_categories', key: 'target_categories', ellipsis: true },
    { title: '我的状态', dataIndex: 'my_status', key: 'my_status', render: (v: string, r: any) => {
      const key = v || r.status
      const s = projectStatusMap[key] || { color: 'default', text: key }
      return <Tag color={s.color}>{s.text}</Tag>
    }},
    { title: '截止日期', dataIndex: 'deadline', key: 'deadline', render: (v: string) => v ? new Date(v).toLocaleDateString() : '-' },
    { title: '操作', key: 'action', render: (_: any, r: any) => (
      <Space>
        <Button type="link" icon={<EyeOutlined />} size="small" onClick={() => handleView(r)}>查看</Button>
        {(r.my_status === 'pending_response' || r.my_status === 'supplement_materials') && (
          <Button type="primary" icon={<FileTextOutlined />} size="small" onClick={() => handleFill(r)}>填写问卷</Button>
        )}
      </Space>
    )},
  ]

  const renderField = (field: any) => {
    if (field.type === 'select') {
      return (
        <Select placeholder={field.placeholder || '请选择'}>
          {(field.options || []).map((o: any) => {
            const val = typeof o === 'string' ? o : o.value
            const label = typeof o === 'string' ? o : o.label
            return <Select.Option key={val} value={val}>{label}</Select.Option>
          })}
        </Select>
      )
    }
    if (field.type === 'textarea') {
      return <Input.TextArea rows={3} placeholder={field.placeholder || '请输入'} />
    }
    if (field.type === 'number') {
      return <InputNumber style={{ width: '100%' }} placeholder={field.placeholder || '请输入'} />
    }
    if (field.type === 'file') {
      return (
        <div>
          <Button icon={<UploadOutlined />}>上传文件</Button>
          {field.note && <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>{field.note}</span>}
        </div>
      )
    }
    return <Input placeholder={field.placeholder || '请输入'} />
  }

  return (
    <div>
      <Card title="资格评审项目 (US-104-2)">
        <Table rowKey="id" dataSource={data} columns={columns} loading={loading} pagination={{ pageSize: 10 }} />
      </Card>

      <Modal title="评审项目详情 (US-104-2)" open={viewOpen} onCancel={() => setViewOpen(false)} footer={null} width={640}>
        {viewDetail && (
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item label="项目名称">{viewDetail.project_name}</Descriptions.Item>
            <Descriptions.Item label="评审品类">{viewDetail.target_categories || '-'}</Descriptions.Item>
            <Descriptions.Item label="截止日期">{viewDetail.deadline ? new Date(viewDetail.deadline).toLocaleDateString() : '-'}</Descriptions.Item>
            <Descriptions.Item label="项目状态">
              <Tag color={projectStatusMap[viewDetail.status]?.color}>{projectStatusMap[viewDetail.status]?.text || viewDetail.status}</Tag>
            </Descriptions.Item>
            {viewDetail.notes && <Descriptions.Item label="评审要求">{viewDetail.notes}</Descriptions.Item>}
          </Descriptions>
        )}
      </Modal>

      <Modal
        title={`填写资格问卷 (US-105) - ${currentProject?.project_name || ''}`}
        open={fillOpen}
        onOk={handleSubmit}
        onCancel={() => { setFillOpen(false); form.resetFields() }}
        width={720}
        okText="提交问卷"
      >
        <Form form={form} layout="vertical">
          {questionnaire?.sections && Array.isArray(questionnaire.sections) ? (
            <Collapse
              defaultActiveKey={questionnaire.sections.map((s: any) => s.id)}
              items={questionnaire.sections.map((section: any) => ({
                key: section.id,
                label: section.title,
                children: (section.fields || []).map((field: any) => (
                  <Form.Item
                    key={field.id}
                    name={field.id}
                    label={field.label}
                    rules={field.required ? [{ required: true, message: '请填写' }] : undefined}
                  >
                    {renderField(field)}
                  </Form.Item>
                ))
              }))}
            />
          ) : (
            <>
              <Form.Item name="company_qualification" label="企业资质等级" rules={[{ required: true }]}>
                <Select placeholder="请选择">
                  <Select.Option value="AAA">AAA级</Select.Option>
                  <Select.Option value="AA">AA级</Select.Option>
                  <Select.Option value="A">A级</Select.Option>
                  <Select.Option value="B">B级</Select.Option>
                </Select>
              </Form.Item>
              <Form.Item name="quality_system" label="质量管理体系认证" rules={[{ required: true }]}>
                <Input placeholder="如：ISO 9001, HACCP等" />
              </Form.Item>
              <Form.Item name="production_capacity" label="年产能（吨）" rules={[{ required: true }]}>
                <Input type="number" placeholder="年产能" />
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default SupplierQualification
