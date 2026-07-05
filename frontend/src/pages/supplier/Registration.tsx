import React, { useEffect, useState, useCallback } from 'react'
import { Card, Form, Input, Button, Steps, Result, Descriptions, Tag, message } from 'antd'
import { UserOutlined, MailOutlined, PhoneOutlined, HomeOutlined, SearchOutlined } from '@ant-design/icons'
import { useSearchParams } from 'react-router-dom'
import { registerSupplier, validateInvitationCode, getRegistrationStatus } from '../../api'

const SupplierRegistration: React.FC = () => {
  const [searchParams] = useSearchParams()
  const [step, setStep] = useState(0)
  const [invitationInfo, setInvitationInfo] = useState<any>(null)
  const [statusData, setStatusData] = useState<any>(null)
  const [statusLoading, setStatusLoading] = useState(false)
  const [statusUcc, setStatusUcc] = useState('')
  const [form] = Form.useForm()
  const [codeForm] = Form.useForm()

  const handleValidateCode = useCallback(async (codeOverride?: string) => {
    try {
      const code = (codeOverride ?? (await codeForm.validateFields()).code)?.trim().toUpperCase()
      if (!code) return
      const res = await validateInvitationCode(code) as any
      if (res.valid) {
        setInvitationInfo(res)
        form.setFieldsValue({
          invitation_code: code,
          company_name: res.invited_supplier_name || undefined,
          contact_email: res.invited_email || undefined,
        })
        setStep(1)
      } else {
        message.error(res.message || '邀请码无效')
      }
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('验证失败')
    }
  }, [codeForm, form])

  useEffect(() => {
    const code = searchParams.get('code')?.trim().toUpperCase()
    if (code) {
      codeForm.setFieldsValue({ code })
      handleValidateCode(code)
    }
  }, [searchParams, codeForm, handleValidateCode])

  // 提交注册
  const handleRegister = async () => {
    try {
      const values = await form.validateFields()
      const res = await registerSupplier(values) as any
      setStep(2)
      message.success('注册成功')
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('注册失败')
    }
  }

  // 查询注册状态（按统一社会信用代码）
  const handleCheckStatus = async () => {
    if (!statusUcc.trim()) { message.warning('请输入统一社会信用代码'); return }
    try {
      setStatusLoading(true)
      const res = await getRegistrationStatus(statusUcc.trim()) as any
      setStatusData(res)
    } catch { message.error('查询失败') }
    finally { setStatusLoading(false) }
  }

  return (
    <div style={{ maxWidth: 680, margin: '0 auto' }}>
      <Card title="供应商自助注册 (US-102)">
        <Steps current={step} items={[{ title: '验证邀请码' }, { title: '填写信息' }, { title: '完成' }]} style={{ marginBottom: 24 }} />

        {step === 0 && (
          <>
            <Form form={codeForm} layout="vertical" style={{ maxWidth: 400, margin: '0 auto' }}>
              <Form.Item name="code" label="邀请码" rules={[{ required: true, message: '请输入邀请码' }]}>
                <Input.Search placeholder="请输入8位邀请码" maxLength={8} enterButton="验证" onSearch={() => handleValidateCode()} size="large" style={{ textTransform: 'uppercase' }} />
              </Form.Item>
            </Form>
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              <div style={{ maxWidth: 400, margin: '0 auto' }}>
                <Input.Search
                  placeholder="输入统一社会信用代码查询注册状态"
                  value={statusUcc}
                  onChange={e => setStatusUcc(e.target.value)}
                  enterButton={<><SearchOutlined /> 查询状态</>}
                  loading={statusLoading}
                  onSearch={handleCheckStatus}
                  maxLength={18}
                />
              </div>
            </div>
            {statusData && (
              <Card size="small" style={{ marginTop: 16 }}>
                <Descriptions bordered column={1} size="small">
                  <Descriptions.Item label="公司名称">{statusData.company_name || '-'}</Descriptions.Item>
                  <Descriptions.Item label="状态">
                    <Tag color={statusData.status === 'approved' ? 'green' : statusData.status === 'rejected' ? 'red' : 'orange'}>
                      {statusData.found === false ? '未找到记录' : statusData.status || '未知'}
                    </Tag>
                  </Descriptions.Item>
                  {statusData.audit_opinion && <Descriptions.Item label="审核意见">{statusData.audit_opinion}</Descriptions.Item>}
                </Descriptions>
              </Card>
            )}
          </>
        )}

        {step === 1 && (
          <Form form={form} layout="vertical">
            <Form.Item name="invitation_code" label="邀请码" rules={[{ required: true }]}>
              <Input disabled />
            </Form.Item>
            <Form.Item name="company_name" label="公司名称" rules={[{ required: true, message: '请输入公司名称' }]}>
              <Input prefix={<HomeOutlined />} placeholder="公司全称" />
            </Form.Item>
            <Form.Item name="unified_credit_code" label="统一社会信用代码" rules={[{ required: true, message: '请输入统一社会信用代码' }]}>
              <Input placeholder="18位统一社会信用代码" maxLength={18} />
            </Form.Item>
            <Form.Item name="contact_person" label="联系人" rules={[{ required: true, message: '请输入联系人' }]}>
              <Input prefix={<UserOutlined />} placeholder="联系人姓名" />
            </Form.Item>
            <Form.Item name="contact_phone" label="联系电话" rules={[{ required: true, message: '请输入联系电话' }]}>
              <Input prefix={<PhoneOutlined />} placeholder="手机号码" />
            </Form.Item>
            <Form.Item name="contact_email" label="邮箱">
              <Input prefix={<MailOutlined />} placeholder="name@company.com" />
            </Form.Item>
            <Form.Item name="main_categories" label="主营品类">
              <Input.TextArea rows={2} placeholder="如：高粱、小麦等原料" />
            </Form.Item>
            <Form.Item name="address" label="地址">
              <Input placeholder="公司注册地址" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" onClick={handleRegister} size="large" block>提交注册</Button>
            </Form.Item>
          </Form>
        )}

        {step === 2 && (
          <Result status="success" title="注册提交成功" subTitle="您的注册信息已提交，请等待采购方审核。" extra={[
            <Button key="back" onClick={() => { setStep(0); form.resetFields(); codeForm.resetFields() }}>返回</Button>
          ]} />
        )}
      </Card>
    </div>
  )
}

export default SupplierRegistration
