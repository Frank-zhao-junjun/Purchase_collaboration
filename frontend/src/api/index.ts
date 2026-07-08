import api from './request'

// Dashboard API
export const getDashboardMetrics = () => api.get('/dashboard/stats')
export const getAlerts = () => api.get('/dashboard/inventory-alerts')
export const getTodos = () => Promise.resolve([]) // 暂无
export const getFulfillmentStatus = () => Promise.resolve([]) // 暂无
export const getOrderTrends = (days = 7) => Promise.resolve([]) // 暂无

// Suppliers API
export const getSuppliers = (params = {}) => api.get('/suppliers/', { params })
export const getSupplierStats = () => Promise.resolve({}) // 暂无

// Purchase Orders API (后端使用 purchase-orders)
export const getOrders = (params = {}) => api.get('/purchase-orders/', { params })
export const getOrderById = (id: number | string) => api.get(`/purchase-orders/${id}`)
export const getOrderStats = () => Promise.resolve({}) // 暂无

// Materials/Inventory API (后端使用 materials)
export const getInventory = (params = {}) => api.get('/materials/', { params })
export const getInventoryStats = () => api.get('/dashboard/stats')
export const getInventoryAlerts = () => api.get('/materials/low-stock')

// Inspections API - 使用生产记录代替
export const getInspections = (params = {}) => api.get('/production/records', { params })
export const getInspectionStats = () => api.get('/production/today-stats')

// Waybills API - 暂无
export const getWaybills = (params = {}) => Promise.resolve([])

// Batches API - 使用生产记录
export const getBatches = (params = {}) => api.get('/production/records', { params })

// Products API
export const getProducts = (params = {}) => api.get('/products/', { params })
export const getProductCategories = () => api.get('/products/categories')
export const getProductBrands = () => api.get('/products/brands')

// Sales Orders API
export const getSalesOrders = (params = {}) => api.get('/sales-orders/', { params })

// Warehouses API
export const getWarehouses = (params = {}) => api.get('/warehouses/', { params })

// ============ 供应商准入 API (Phase 1) ============

// US-101: 注册邀请
export const createInvitation = (data: {
  invited_supplier_name: string
  invited_email: string
  invited_contact_person?: string
  notes?: string
  expiry_days?: number
}) => api.post('/supplier-portal/invitations', data)

export const getInvitations = (params?: { status?: string; email?: string }) =>
  api.get('/supplier-portal/invitations', { params })

export const deleteInvitation = (id: number) =>
  api.delete(`/supplier-portal/invitations/${id}`)

export const validateInvitationCode = (code: string) =>
  api.get(`/supplier-portal/invitations/${code}/validate`)

// US-102: 供应商自助注册
export const registerSupplier = (data: {
  invitation_code: string
  company_name: string
  unified_credit_code: string
  contact_person: string
  contact_phone: string
  contact_email?: string
  address?: string
  main_categories?: string
  annual_capacity?: number
  employee_count?: number
  established_year?: number
}) => api.post('/supplier-portal/register', data)

export const getRegistrationStatus = (unifiedCreditCode: string) =>
  api.get('/supplier-portal/register/status', { params: { unified_credit_code: unifiedCreditCode } })

// US-103: 注册审核
export const getPendingAuditRegistrations = () =>
  api.get('/supplier-portal/pending-audit')

export const getRegistration = (id: number) =>
  api.get(`/supplier-portal/registrations/${id}`)

export const auditRegistration = (id: number, data: {
  action: 'approve' | 'reject'
  opinion?: string
}) => api.post(`/supplier-portal/registrations/${id}/audit`, data)

export const resubmitRegistration = (id: number, data: {
  company_name: string
  unified_credit_code: string
  contact_person: string
  contact_phone: string
  contact_email?: string
  address?: string
  main_categories?: string
  annual_capacity?: number
}) => api.post(`/supplier-portal/registrations/${id}/resubmit`, data)

// US-104~107: 资格评审
export const createQualificationProject = (data: {
  project_name: string
  target_categories: string
  target_supplier_ids: number[]
  notes?: string
  deadline?: string
}) => api.post('/qualification/projects', data)

export const getQualificationProjects = (params?: { status?: string; supplier_id?: number }) =>
  api.get('/qualification/projects', { params })

export const getQualificationProject = (id: number) =>
  api.get(`/qualification/projects/${id}`)

export const getQuestionnaire = (projectId: number, config?: { params?: Record<string, any> }) =>
  api.get(`/qualification/projects/${projectId}/questionnaire`, config)

// US-105: 供应商填写问卷
export const submitQualification = (projectId: number, data: {
  supplier_id: number
  answers: Record<string, unknown>
}) => api.post(`/qualification/projects/${projectId}/submission`, data)

export const getQualificationSubmissions = (projectId: number) =>
  api.get(`/qualification/projects/${projectId}/submissions`)

export const getQualificationSubmission = (projectId: number, supplierId: number) =>
  api.get(`/qualification/projects/${projectId}/submissions/${supplierId}`)

// US-106: 评审
export const reviewQualification = (projectId: number, supplierId: number, data: {
  reviewer_id?: number
  tech_score?: number
  quality_score?: number
  finance_score?: number
  opinions?: string
  clarification_message?: string
}) => api.post(`/qualification/projects/${projectId}/submissions/${supplierId}/review`, data)

// US-107: 审批
export const approveQualification = (projectId: number, supplierId: number, opinion = '') =>
  api.post(`/qualification/projects/${projectId}/approve?supplier_id=${supplierId}&opinion=${encodeURIComponent(opinion)}`)

export const rejectQualification = (projectId: number, supplierId: number, reason = '') =>
  api.post(`/qualification/projects/${projectId}/reject?supplier_id=${supplierId}&reason=${encodeURIComponent(reason)}`)

export const getQualificationStatus = (projectId: number) =>
  api.get(`/qualification/projects/${projectId}/status`)

// US-108: 资质过期预警
export const getSupplierCertifications = (supplierId: number) =>
  api.get(`/supplier-portal/suppliers/${supplierId}/certifications`)

export const addSupplierCertification = (supplierId: number, data: {
  cert_type: string
  cert_name: string
  cert_no?: string
  issue_date?: string
  expiry_date: string
  cert_file_url?: string
}) => api.post(`/supplier-portal/suppliers/${supplierId}/certifications`, data)

export const getSupplierAlerts = () =>
  api.get('/supplier-portal/supplier-alerts')

export const resolveAlert = (alertId: number) =>
  api.post(`/supplier-portal/supplier-alerts/${alertId}/resolve`)

export const triggerCertExpiryCheck = () =>
  api.post('/supplier-portal/cert-alerts/check')

// ============ 寻源与合同 API (Phase 2) ============

// 寻源项目
export const getSourcingProjects = (params = {}) => api.get('/sourcing/projects', { params })
export const getSourcingProject = (id: number | string) => api.get(`/sourcing/projects/${id}`)
export const createSourcingProject = (data: any) => api.post('/sourcing/projects', data)
export const openBids = (id: number | string) => api.post(`/sourcing/projects/${id}/open-bids`)
export const awardProject = (id: number | string, winnerSupplierId: number, amount: number) =>
  api.post(`/sourcing/projects/${id}/award?winner_supplier_id=${winnerSupplierId}&awarded_amount=${amount}`)
export const getBidComparison = (id: number | string) => api.get(`/sourcing/projects/${id}/comparison`)

// 合同
export const getContracts = (params = {}) => api.get('/contracts/', { params })
export const getContract = (id: number | string) => api.get(`/contracts/${id}`)
export const initiateSigning = (id: number | string, sequence = 'supplier_first') =>
  api.post(`/contracts/${id}/sign-initiate?sign_sequence=${sequence}`)
export const signContract = (id: number | string, party: 'supplier' | 'buyer') =>
  api.post(`/contracts/${id}/sign?party=${party}`)
export const getContractTemplates = () => api.get('/contracts/templates')
export const generateContractFromSourcing = (sourcingId: number, templateId: number, supplierId: number, contractName: string) =>
  api.post(`/contracts/generate-from-sourcing/${sourcingId}?template_id=${templateId}&supplier_id=${supplierId}&contract_name=${encodeURIComponent(contractName)}`)

// 合同协同
export const acknowledgeContractDraft = (contractId: number) =>
  api.post(`/contracts/drafts/${contractId}/acknowledge`)

export const addContractFeedback = (contractId: number, clauseId: string, party: string, comment: string) =>
  api.post(`/contracts/${contractId}/feedback?clause_id=${encodeURIComponent(clauseId)}&party=${party}&comment=${encodeURIComponent(comment)}`)

export const getContractFeedbackItems = (contractId: number) =>
  api.get(`/contracts/${contractId}/feedback-items`)

// 供应商端 - 邀请
export const getSupplierInvitations = (supplierId: number) =>
  api.get('/sourcing/projects/invitations', { params: { supplier_id: supplierId } })
export const acceptInvitation = (projectId: number, supplierId: number) =>
  api.post(`/sourcing/projects/${projectId}/accept?supplier_id=${supplierId}`)
export const declineInvitation = (projectId: number, supplierId: number, reason = '') =>
  api.post(`/sourcing/projects/${projectId}/decline?supplier_id=${supplierId}&reason=${encodeURIComponent(reason)}`)

// 供应商端 - 投标
export const getBidForm = (projectId: number, supplierId: number) =>
  api.get(`/sourcing/projects/${projectId}/bid`, { params: { supplier_id: supplierId } })
export const submitBid = (projectId: number, data: any) =>
  api.post(`/sourcing/projects/${projectId}/bid`, data)

// ============ 公告栏 API ============

export interface AnnouncementItem {
  id: number
  title: string
  content: string
  announcement_type: 'announcement' | 'policy' | 'guide'
  priority: number
  is_pinned: boolean
  attachments: { name: string; url: string }[]
  published_by: string
  published_at: string
  valid_from: string
  valid_until: string | null
  view_count: number
  created_at: string
}

export interface AnnouncementListResponse {
  total: number
  page: number
  page_size: number
  items: AnnouncementItem[]
}

export const getAnnouncements = (params?: {
  announcement_type?: string
  keyword?: string
  page?: number
  page_size?: number
}) => api.get<AnnouncementListResponse>('/announcements/', { params })

export const getAnnouncement = (id: number) => api.get<AnnouncementItem>(`/announcements/${id}`)

export const createAnnouncement = (data: {
  title: string
  content: string
  announcement_type: string
  priority?: number
  is_pinned?: boolean
  published_by?: string
  valid_until?: string
}) => api.post('/announcements/', data)

export const updateAnnouncement = (id: number, data: Partial<{
  title: string
  content: string
  announcement_type: string
  priority: number
  is_pinned: boolean
  valid_until: string
}>) => api.put(`/announcements/${id}`, data)

export const deleteAnnouncement = (id: number) => api.delete(`/announcements/${id}`)

export const recordAnnouncementRead = (announcementId: number, userId: number) =>
  api.post(`/announcements/${announcementId}/record-read?user_id=${userId}`)

export const getAnnouncementTypesSummary = () =>
  api.get<{ type: string; label: string; count: number }[]>('/announcements/types/summary')

// ============ 物流与入库 API ============

export interface ShipmentNote {
  id: number
  shipment_no: string
  purchase_order_id: number
  supplier_id: number
  supplier_name?: string
  status: string
  carrier_name?: string
  tracking_no?: string
  vehicle_no?: string
  driver_name?: string
  driver_phone?: string
  expected_arrival?: string
  actual_arrival?: string
  shipping_address?: string
  receiving_warehouse?: string
  total_quantity: number
  created_at: string
}

export interface Receipt {
  id: number
  receipt_no: string
  warehouse_id: number
  warehouse_name?: string
  supplier_id: number
  supplier_name?: string
  purchase_order_id?: number
  status: string
  total_quantity: number
  qualified_quantity: number
  unqualified_quantity: number
  inspector?: string
  inspected_at?: string
  remarks?: string
  items: ReceiptItem[]
  created_at: string
}

export interface ReceiptItem {
  id: number
  material_id?: number
  material_name: string
  quantity: number
  unit: string
  batch_no: string
  production_date?: string
  quality_result: string
  warehouse_location?: string
}

// 运单 API
export const getShipmentNotes = (params?: { status?: string; supplier_id?: number }) =>
  api.get<ShipmentNote[]>('/logistics/shipment-notes/', { params })

export const getShipmentNote = (id: number) =>
  api.get<ShipmentNote>(`/logistics/shipment-notes/${id}`)

export const confirmArrival = (id: number) =>
  api.post(`/logistics/shipment-notes/${id}/arrive`)

// 入库单 API
export const getReceipts = (params?: { status?: string; warehouse_id?: number; supplier_id?: number; keyword?: string }) =>
  api.get<Receipt[]>('/logistics/receipts/', { params })

export const getReceipt = (id: number) =>
  api.get<Receipt>(`/logistics/receipts/${id}`)

export const createReceipt = (data: {
  receipt_no?: string
  asn_id?: number
  warehouse_id: number
  supplier_id: number
  purchase_order_id?: number
  remarks?: string
  items: {
    material_id?: number
    material_name: string
    quantity: number
    unit: string
    batch_no: string
    quality_result: string
    warehouse_location?: string
  }[]
}) => api.post('/logistics/receipts/', data)

export const getReceiptStats = () =>
  api.get('/logistics/receipts/stats/summary')

// ============ 财务管理 API ============

export interface SettlementStatement {
  id: number
  statement_no: string
  supplier_id: number
  supplier_name?: string
  period_start: string
  period_end: string
  total_amount: number
  paid_amount: number
  unpaid_amount: number
  status: string
  confirmed_at?: string
  confirmed_by?: string
  remarks?: string
  created_at: string
}

export interface Invoice {
  id: number
  invoice_no: string
  statement_id?: number
  supplier_id: number
  supplier_name?: string
  amount: number
  tax_amount: number
  total_amount: number
  invoice_type: string
  invoice_date?: string
  status: string
  remarks?: string
  created_at: string
}

export interface Payment {
  id: number
  payment_no: string
  invoice_id?: number
  statement_id?: number
  supplier_id: number
  supplier_name?: string
  amount: number
  payment_method: string
  expected_date?: string
  actual_date?: string
  status: string
  pre_payment: boolean
  remarks?: string
  created_at: string
}

// 结算单 API
export const getStatements = (params?: { status?: string; supplier_id?: number; keyword?: string }) =>
  api.get<SettlementStatement[]>('/financial/statements/', { params })

export const getStatement = (id: number) =>
  api.get<SettlementStatement>(`/financial/statements/${id}`)

export const createStatement = (data: {
  statement_no?: string
  supplier_id: number
  period_start: string
  period_end: string
  total_amount: number
  receipt_ids?: number[]
  settlement_period?: string
  remarks?: string
}, submit = false) => api.post('/financial/statements/', data, { params: submit ? { submit: 'true' } : {} })

export const updateStatement = (id: number, data: {
  supplier_id: number
  period_start: string
  period_end: string
  total_amount: number
  receipt_ids?: number[]
  settlement_period?: string
  remarks?: string
}, submit = false) => api.put(`/financial/statements/${id}`, data, { params: submit ? { submit: 'true' } : {} })

export const buyerAuditStatement = (id: number, data: {
  action: 'approve' | 'reject'
  auditor?: string
  message?: string
}) => api.post(`/financial/statements/${id}/buyer-audit`, data)

export const confirmStatement = (id: number, confirmed_by?: string) =>
  api.post(`/financial/statements/${id}/confirm?confirmed_by=${confirmed_by || ''}`)

export const getStatementStats = () =>
  api.get('/financial/statements/stats/summary')

// 发票 API
export const getInvoices = (params?: { status?: string; supplier_id?: number; keyword?: string }) =>
  api.get<Invoice[]>('/financial/invoices/', { params })

export const getInvoice = (id: number) =>
  api.get<Invoice>(`/financial/invoices/${id}`)

export const createInvoice = (data: {
  invoice_no?: string
  statement_id?: number
  supplier_id: number
  amount: number
  tax_amount: number
  invoice_type?: string
  invoice_date?: string
  remarks?: string
}) => api.post('/financial/invoices/', data)

export const getInvoiceStats = () =>
  api.get('/financial/invoices/stats/summary')

// 付款 API
export const getPayments = (params?: { status?: string; supplier_id?: number; keyword?: string }) =>
  api.get<Payment[]>('/financial/payments/', { params })

export const getPayment = (id: number) =>
  api.get<Payment>(`/financial/payments/${id}`)

export const createPayment = (data: {
  payment_no?: string
  invoice_id?: number
  statement_id?: number
  supplier_id: number
  amount: number
  payment_method?: string
  expected_date?: string
  remarks?: string
}) => api.post('/financial/payments/', data)

export const approvePayment = (id: number) =>
  api.post(`/financial/payments/${id}/approve`)

export const confirmPayment = (id: number) =>
  api.post(`/financial/payments/${id}/pay`)

export const getPaymentStats = () =>
  api.get('/financial/payments/stats/summary')

// ============ 预测与订单执行 API (Phase 3) ============

// US-301: 采购预测 (供应商视角)
export const getForecasts = (params?: { supplier_id?: number; status?: string }) =>
  api.get('/supplier-portal/forecasts', { params })

export const getForecastDetail = (forecastId: number, params?: { supplier_id?: number }) =>
  api.get(`/supplier-portal/forecasts/${forecastId}`, { params })

// US-302: 供应商产能响应
export const submitCapacityResponse = (forecastId: number, data: {
  forecast_id: number
  supplier_id: number
  items: { material_id: number; material_name?: string; committed_qty: number; committed_date?: string; risk_level?: string }[]
  risk_summary?: string
}) => api.post(`/supplier-portal/forecasts/${forecastId}/respond`, data)

// US-303: 采购订单 - 供应商确认/拒绝
export const getSupplierOrders = (params?: { supplier_id?: number; status?: string }) =>
  api.get('/supplier-portal/orders', { params })

export const confirmOrder = (id: number, supplierId: number) =>
  api.post(`/supplier-portal/orders/${id}/confirm?supplier_id=${supplierId}`, { action: 'confirm' })

export const rejectOrder = (id: number, supplierId: number, reason: string) =>
  api.post(`/supplier-portal/orders/${id}/confirm?supplier_id=${supplierId}`, { action: 'reject', rejection_reason: reason })

// US-305: 要货计划 (供应商视角)
export const getDeliveryPlans = (params?: { supplier_id?: number; status?: string }) =>
  api.get('/supplier-portal/delivery-schedules', { params })

// US-306: 供应商确认要货计划
export const confirmDeliveryPlan = (planId: number, data: {
  confirmed: boolean
  adjustment_notes?: string
  adjusted_quantities?: Record<string, number>
}) => api.post(`/supplier-portal/delivery-schedules/${planId}/confirm`, data)

// US-307: ASN / 送货计划 (供应商视角)
export const getASNList = (params?: { supplier_id?: number; status?: string }) =>
  api.get('/supplier-portal/asns', { params })

export const createASN = (data: {
  po_id: number
  supplier_id: number
  delivery_schedule_id?: number
  asn_no?: string
  carrier_name?: string
  carrier_contact?: string
  tracking_no?: string
  items: { material_id?: number; material_name?: string; quantity: number; batch_no?: string; production_date?: string }[]
}) => api.post('/supplier-portal/asns', data)

export const submitASN = (asnId: number) =>
  api.post(`/supplier-portal/asns/${asnId}/submit`)

// US-308: 采购方确认送货计划
export const approveASN = (id: number) =>
  api.post(`/logistics/shipment-notes/${id}/approve`)

export const rejectASN = (id: number, reason: string) =>
  api.post(`/logistics/shipment-notes/${id}/reject?reason=${encodeURIComponent(reason)}`)

// US-309: 装箱单与批次
export const getPackingLists = (asnId: number) =>
  api.get(`/logistics/shipment-notes/${asnId}/packing-lists`).catch(() => [])

export const submitPackingList = (asnId: number, data: {
  items: { material_name: string; quantity: number; batch_no: string; production_date?: string }[]
}) => api.post(`/logistics/shipment-notes/${asnId}/packing-lists`, data)

// US-310: 收货与验收 (WMS/QMS 同步)
export const getReceiptAndInspection = (params?: { keyword?: string }) =>
  api.get('/logistics/receipts/', { params: { ...params, include_inspection: true } })

// US-401~405: 财务结算 (已有上方 API)
// 补充：供应商端结算单审批拒绝
export const rejectStatement = (id: number, reason: string) =>
  api.post(`/financial/statements/${id}/reject?reason=${encodeURIComponent(reason)}`)

export const addStatementComment = (id: number, data: { comment: string; author: string }) =>
  api.post(`/financial/statements/${id}/comments`, data)

// US-404: 三单匹配与发票审批
export const threeWayMatch = (invoiceId: number) =>
  api.get(`/financial/invoices/${invoiceId}/three-way-match`)

export const approveInvoice = (id: number) =>
  api.post(`/financial/invoices/${id}/approve`)

export const rejectInvoice = (id: number, reason: string) =>
  api.post(`/financial/invoices/${id}/reject?reason=${encodeURIComponent(reason)}`)

export const resubmitInvoice = (id: number, data: {
  supplier_id: number
  statement_id?: number
  amount: number
  tax_amount: number
  remarks?: string
  invoice_image_url?: string
}) => api.post(`/financial/invoices/${id}/resubmit`, data)


// ============ US-301: 采购预测 Excel 导入 ============
export const importForecastExcel = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/supplier-portal/forecasts/import-excel', formData, {
    timeout: 60000,
  })
}

