import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import Layout from './components/Layout'
import Login from './pages/Login'
import { getSession } from './auth'

// 采购端页面
import BuyerHome from './pages/buyer/BuyerHome'
import InvitationList from './pages/buyer/InvitationList'
import RegistrationAudit from './pages/buyer/RegistrationAudit'
import QualificationProjectList from './pages/buyer/QualificationProjectList'
import CertAlertList from './pages/buyer/CertAlertList'
import SourcingList from './pages/buyer/SourcingList'
import SourcingDetail from './pages/buyer/SourcingDetail'
import ContractList from './pages/buyer/ContractList'
import ForecastList from './pages/buyer/ForecastList'
import PurchaseOrderList from './pages/PurchaseOrderList'
import DeliveryPlanList from './pages/buyer/DeliveryPlanList'
import WaybillList from './pages/WaybillList'
import ReceiptList from './pages/ReceiptList'
import InventoryList from './pages/InventoryList'
import InspectionList from './pages/InspectionList'
import FinancialList from './pages/FinancialList'
import BuyerAnnouncementList from './pages/buyer/AnnouncementList'
import SupplierList from './pages/SupplierList'

// 供应商端页面
import SupplierHome from './pages/supplier/SupplierHome'
import SupplierRegistration from './pages/supplier/Registration'
import SupplierQualification from './pages/supplier/QualificationList'
import SupplierCertification from './pages/supplier/CertificationList'
import SupplierInvitationList from './pages/supplier/InvitationList'
import RegistrationInvitationList from './pages/supplier/RegistrationInvitationList'
import BidList from './pages/supplier/BidList'
import SupplierContractList from './pages/supplier/ContractList'
import SupplierOrderConfirm from './pages/supplier/OrderConfirm'
import CapacityResponse from './pages/supplier/CapacityResponse'
import SupplierDeliveryPlan from './pages/supplier/DeliveryPlanList'
import ASNList from './pages/supplier/ASNList'
import SupplierSettlement from './pages/supplier/SettlementList'
import SupplierInvoice from './pages/supplier/InvoiceList'
import SupplierAnnouncementList from './pages/supplier/AnnouncementList'

const theme = { token: { colorPrimary: '#3E5BF2', borderRadius: 4 } }

// 登录守卫：未携带有效会话时展示登录页（SEC-001 前端配套）
function RequireAuth({ children }: { children: React.ReactNode }) {
  const session = getSession()
  if (!session) {
    return <Login />
  }
  return <>{children}</>
}

function App() {
  return (
    <ConfigProvider theme={theme} locale={zhCN}>
      <BrowserRouter>
        <RequireAuth>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/buyer" replace />} />

            {/* 采购端 */}
            <Route path="buyer">
              <Route index element={<BuyerHome />} />
              {/* Phase 1: 供应商准入 */}
              <Route path="invitations" element={<InvitationList />} />
              <Route path="registrations" element={<RegistrationAudit />} />
              <Route path="qualifications" element={<QualificationProjectList />} />
              <Route path="cert-alerts" element={<CertAlertList />} />
              {/* Phase 2: 寻源与合同 */}
              <Route path="sourcing" element={<SourcingList />} />
              <Route path="sourcing/:id" element={<SourcingDetail />} />
              <Route path="contracts" element={<ContractList />} />
              {/* Phase 3: 采购执行 */}
              <Route path="forecast" element={<ForecastList />} />
              <Route path="orders" element={<PurchaseOrderList />} />
              <Route path="delivery-plans" element={<DeliveryPlanList />} />
              {/* 仓储物流 */}
              <Route path="waybills" element={<WaybillList />} />
              <Route path="receipts" element={<ReceiptList />} />
              <Route path="inventory" element={<InventoryList />} />
              <Route path="inspections" element={<InspectionList />} />
              {/* Phase 4: 财务 */}
              <Route path="financial" element={<FinancialList />} />
              {/* 其他 */}
              <Route path="suppliers" element={<SupplierList />} />
              <Route path="announcements" element={<BuyerAnnouncementList />} />
            </Route>

            {/* 供应商端 */}
            <Route path="supplier">
              <Route index element={<SupplierHome />} />
              {/* Phase 1: 供应商准入 */}
              <Route path="registration" element={<SupplierRegistration />} />
              <Route path="registration-invitations" element={<RegistrationInvitationList />} />
              <Route path="qualifications" element={<SupplierQualification />} />
              <Route path="certifications" element={<SupplierCertification />} />
              {/* Phase 2: 寻源协同 */}
              <Route path="invitations" element={<SupplierInvitationList />} />
              <Route path="bids" element={<BidList />} />
              {/* Phase 3: 订单执行 */}
              <Route path="orders" element={<SupplierOrderConfirm />} />
              <Route path="order-confirm" element={<SupplierOrderConfirm />} />
              <Route path="capacity" element={<CapacityResponse />} />
              <Route path="delivery-plans" element={<SupplierDeliveryPlan />} />
              <Route path="asn" element={<ASNList />} />
              <Route path="contracts" element={<SupplierContractList />} />
              {/* Phase 4: 财务结算 */}
              <Route path="settlements" element={<SupplierSettlement />} />
              <Route path="invoices" element={<SupplierInvoice />} />
              {/* 信息共享 */}
              <Route path="announcements" element={<SupplierAnnouncementList />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
