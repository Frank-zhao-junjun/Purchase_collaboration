import React, { useEffect, useState, useCallback } from 'react'
import { Card, Form, Input, InputNumber, Button, Steps, Result, Descriptions, Tag, message, Alert } from 'antd'
import { UserOutlined, MailOutlined, PhoneOutlined, HomeOutlined, SearchOutlined } from '@ant-design/icons'
import { useSearchParams } from 'react-router-dom'
import {
  registerSupplier, validateInvitationCode, getRegistrationStatus, resubmitRegistration,
} from '../../api'

const statusLabels: Record<string, { color: string; text: string }> = {
  pending_audit: { color: 'orange', text: '待审核' },
  auditing: { color: 'blue', text: '审核中' },
  approved: { color: 'green', text: '已通过' },
  rejected: { color: 'red', text: '已驳回' },
}

const SupplierRegistration: React.FC = () => {
  const [searchParams] = useSearchParams()
  const [step, setStep] = useState(0)
  const [invitationInfo, setInvitationInfo] = useState<any>(null)
  const [statusData, setStatusData] = useState<any>(null)
  const [statusLoading, setStatusLoading] = useState(false)
  const [statusUcc, setStatusUcc] = useState('')
  const [resubmitLoading, setResubmitLoading] = useState(false)
  const [form] = Form.useForm()
  const [codeForm] = Form.useForm()
  const [resubmitForm] = Form.useForm()

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

  const handleRegister = async () => {
    try {
      const values = await form.validateFields()
      await registerSupplier(values)
      setStep(2)
      message.success('注册成功')
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('注册失败')
    }
  }

  const handleCheckStatus = async (ucc?: string) => {
    const query = (ucc ?? statusUcc).trim()
    if (!query) { message.warning('请输入统一社会信用代码'); return }
    try {
      setStatusLoading(true)
      const res = await getRegistrationStatus(query) as any
      setStatusData(res)
      if (res.found && res.status === 'rejected') {
        resubmitForm.setFieldsValue({
          company_name: res.company_name,
          unified_credit_code: res.unified_credit_code,
          contact_person: res.contact_person,
          contact_phone: res.contact_phone,
          contact_email: res.contact_email,
          address: res.address,
          main_categories: res.main_categories,
          annual_capacity: res.annual_capacity,
        })
      }
    } catch { message.error('查询失败') }
    finally { setStatusLoading(false) }
  }

  const handleResubmit = async () => {
    if (!statusData?.id) return
    try {
      const values = await resubmitForm.validateFields()
      setResubmitLoading(true)
      await resubmitRegistration(statusData.id, values)
      message.success('已重新提交，请等待采购方审核')
      await handleCheckStatus(values.unified_credit_code)
    } catch (e: any) {
      if (e?.errorFields) return
      message.error('重新提交失败')
    } finally {
      setResubmitLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 680, margin: '0 auto' }}>
      <Card title="供应商自助注册 (US-102-1 / US-103-2)">
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
                  placeholder="输入统一社会信用代码查询注册状态 (US-103-2)"
                  value={statusUcc}
                  onChange={e => setStatusUcc(e.target.value)}
                  enterButton={<><SearchOutlined /> 查询状态</>}
                  loading={statusLoading}
                  onSearch={() => handleCheckStatus()}
                  maxLength={18}
                />
              </div>
            </div>
            {statusData && (
              <Card size="small" style={{ marginTop: 16 }} title="注册状态">
                <Descriptions bordered column={1} size="small">
                  <Descriptions.Item label="公司名称">{statusData.company_name || '-'}</Descriptions.Item>
                  <Descriptions.Item label="状态">
                    {statusData.found === false ? (
                      <Tag>未找到记录</Tag>
                    ) : (
                      <Tag color={statusLabels[statusData.status]?.color || 'default'}>
                        {statusLabels[statusData.status]?.text || statusData.status || '未知'}
                      </Tag>
                    )}
                  </Descriptions.Item>
                  {statusData.audit_opinion && (
                    <Descriptions.Item label="审核意见">{statusData.audit_opinion}</Descriptions.Item>
                  )}
                </Descriptions>
                {statusData.found && statusData.status === 'rejected' && (
                  <>
                    <Alert
                      type="warning"
                      showIcon
                      style={{ marginTop: 16 }}
                      message="注册申请已被驳回"
                      description="请根据采购方审核意见修订资料后重新提交。"
                    />
                    <Form form={resubmitForm} layout="vertical" style={{ marginTop: 16 }}>
                      <Form.Item name="company_name" label="公司名称" rules={[{ required: true }]}>
                        <Input prefix={<HomeOutlined />} />
                      </Form.Item>
                      <Form.Item name="unified_credit_code" label="统一社会信用代码" rules={[{ required: true }]}>
                        <Input disabled />
                      </Form.Item>
                      <Form.Item name="contact_person" label="联系人" rules={[{ required: true }]}>
                        <Input prefix={<UserOutlined />} />
                      </Form.Item>
                      <Form.Item name="contact_phone" label="联系电话" rules={[{ required: true }]}>
                        <Input prefix={<PhoneOutlined />} />
                      </Form.Item>
                      <Form.Item name="contact_email" label="邮箱">
                        <Input prefix={<MailOutlined />} />
                      </Form.Item>
                      <Form.Item name="main_categories" label="主营品类">
                        <Input.TextArea rows={2} />
                      </Form.Item>
                      <Form.Item name="annual_capacity" label="年供货能力(吨)">
                        <InputNumber min={0} style={{ width: '100%' }} />
                      </Form.Item>
                      <Form.Item name="address" label="地址">
                        <Input />
                      </Form.Item>
                      <Button type="primary" block loading={resubmitLoading} onClick={handleResubmit}>
                        重新提交 (US-103-2)
                      </Button>
                    </Form>
                  </>
                )}
              </Card>
            )}
          </>
        )}

        {step === 1 && (
          <>
            {invitationInfo && (
              <Alert
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
                message={`受邀企业：${invitationInfo.invited_supplier_name || '-'} · 邮箱：${invitationInfo.invited_email || '-'}`}
              />
            )}
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
          </>
        )}

        {step === 2 && (
          <Result
            status="success"
            title="注册提交成功"
            subTitle="您的注册信息已提交，请等待采购方审核。"
            extra={[
              <Button key="back" onClick={() => { setStep(0); form.resetFields(); codeForm.resetFields(); setStatusData(null) }}>返回</Button>,
            ]}
          />
        )}
      </Card>
    </div>
  )
}

export default SupplierRegistration
