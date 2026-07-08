import React, { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { clearSession } from '../auth'
import { Layout as AntLayout, Menu, Badge, Dropdown, Button } from 'antd'
import {
  DashboardOutlined, FileTextOutlined, TeamOutlined, ShoppingOutlined,
  InboxOutlined, AppstoreOutlined, AuditOutlined, SwapOutlined,
  TrophyOutlined, ThunderboltOutlined, ContainerOutlined, MessageOutlined,
  BellOutlined, CarOutlined, DollarOutlined, SafetyCertificateOutlined,
  ScheduleOutlined, FileProtectOutlined, SendOutlined, BarcodeOutlined,
  CheckSquareOutlined, AccountBookOutlined, FileSearchOutlined,
  WalletOutlined, FundProjectionScreenOutlined
} from '@ant-design/icons'

const { Sider, Content, Header } = AntLayout

// 采购端菜单
const buyerItems = [
  { key: '/buyer', icon: <DashboardOutlined />, label: '首页概览' },
  { type: 'group' as const, label: '供应商准入', children: [
    { key: '/buyer/invitations', icon: <SendOutlined />, label: '注册邀请' },
    { key: '/buyer/registrations', icon: <TeamOutlined />, label: '注册审核' },
    { key: '/buyer/qualifications', icon: <SafetyCertificateOutlined />, label: '资格评审' },
    { key: '/buyer/cert-alerts', icon: <AuditOutlined />, label: '资质预警' },
  ]},
  { type: 'group' as const, label: '寻源与合同', children: [
    { key: '/buyer/sourcing', icon: <ThunderboltOutlined />, label: '寻源项目' },
    { key: '/buyer/contracts', icon: <TrophyOutlined />, label: '合同管理' },
  ]},
  { type: 'group' as const, label: '采购执行', children: [
    { key: '/buyer/forecast', icon: <FundProjectionScreenOutlined />, label: '采购预测' },
    { key: '/buyer/orders', icon: <FileTextOutlined />, label: '采购订单' },
    { key: '/buyer/delivery-plans', icon: <ScheduleOutlined />, label: '要货计划' },
  ]},
  { type: 'group' as const, label: '仓储物流', children: [
    { key: '/buyer/waybills', icon: <CarOutlined />, label: '运单/ASN' },
    { key: '/buyer/receipts', icon: <InboxOutlined />, label: '入库单' },
    { key: '/buyer/inventory', icon: <AppstoreOutlined />, label: '库存查询' },
    { key: '/buyer/inspections', icon: <AuditOutlined />, label: '质检单' },
  ]},
  { type: 'group' as const, label: '财务管理', children: [
    { key: '/buyer/financial', icon: <DollarOutlined />, label: '结算与付款' },
  ]},
  { type: 'group' as const, label: '系统设置', children: [
    { key: '/buyer/announcements', icon: <BellOutlined />, label: '公告管理' },
  ]},
]

// 供应商端菜单
const supplierItems = [
  { key: '/supplier', icon: <DashboardOutlined />, label: '首页概览' },
  { type: 'group' as const, label: '供应商准入', children: [
    { key: '/supplier/registration-invitations', icon: <SendOutlined />, label: '注册邀请' },
    { key: '/supplier/registration', icon: <FileProtectOutlined />, label: '自助注册' },
    { key: '/supplier/qualifications', icon: <SafetyCertificateOutlined />, label: '资格评审' },
    { key: '/supplier/certifications', icon: <AuditOutlined />, label: '资质管理' },
  ]},
  { type: 'group' as const, label: '寻源协同', children: [
    { key: '/supplier/invitations', icon: <MessageOutlined />, label: '寻源邀请' },
    { key: '/supplier/bids', icon: <SwapOutlined />, label: '投标管理' },
  ]},
  { type: 'group' as const, label: '订单执行', children: [
    { key: '/supplier/order-confirm', icon: <CheckSquareOutlined />, label: '订单确认' },
    { key: '/supplier/capacity', icon: <FundProjectionScreenOutlined />, label: '产能响应' },
    { key: '/supplier/delivery-plans', icon: <ScheduleOutlined />, label: '要货计划' },
    { key: '/supplier/asn', icon: <SendOutlined />, label: '送货计划' },
    { key: '/supplier/contracts', icon: <ContainerOutlined />, label: '合同管理' },
  ]},
  { type: 'group' as const, label: '财务结算', children: [
    { key: '/supplier/settlements', icon: <AccountBookOutlined />, label: '结算单' },
    { key: '/supplier/invoices', icon: <FileSearchOutlined />, label: '发票管理' },
  ]},
  { type: 'group' as const, label: '信息共享', children: [
    { key: '/supplier/announcements', icon: <BellOutlined />, label: '公告通知' },
  ]},
]

function getSelectedKey(pathname: string, portal: string) {
  const prefix = `/${portal}`
  if (pathname === prefix || pathname === `${prefix}/`) return prefix
  if (pathname.startsWith(prefix)) return pathname.split('?')[0]
  return prefix
}

function getMenuItems(portal: string) {
  return portal === 'buyer' ? buyerItems : supplierItems
}

const Layout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const pathParts = location.pathname.split('/').filter(Boolean)
  const [portal, setPortal] = useState<'buyer' | 'supplier'>(
    (pathParts[0] === 'buyer' || pathParts[0] === 'supplier') ? pathParts[0] as 'buyer' | 'supplier' : 'buyer'
  )
  const menuItems = getMenuItems(portal)
  const selectedKey = getSelectedKey(location.pathname, portal)

  const switchPortal = (p: 'buyer' | 'supplier') => {
    setPortal(p)
    navigate(`/${p}`)
  }

  const portalLabel = portal === 'buyer' ? '采购端' : '供应商端'

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{
        background: '#fff', borderBottom: '1px solid #f0f0f0',
        padding: '0 24px', position: 'fixed', width: '100%', zIndex: 100,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: '#1a1a1a' }}>采购供应链协同平台</span>
          <div style={{ display: 'flex', gap: 4, background: '#f5f5f5', borderRadius: 6, padding: 3 }}>
            <Button
              type={portal === 'buyer' ? 'primary' : 'text'}
              size="small"
              onClick={() => switchPortal('buyer')}
              style={{ borderRadius: 4, fontWeight: 600 }}
            >
              采购端
            </Button>
            <Button
              type={portal === 'supplier' ? 'primary' : 'text'}
              size="small"
              onClick={() => switchPortal('supplier')}
              style={{ borderRadius: 4, fontWeight: 600 }}
            >
              供应商端
            </Button>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Badge dot><span style={{ fontSize: 13 }}>{portalLabel}</span></Badge>
          <Dropdown menu={{
            items: [
              { key: 'name', label: portal === 'buyer' ? '张明远' : '贵州红缨子高粱' },
              { key: 'role', label: portal === 'buyer' ? '采购主管' : '供应商管理员' },
              { type: 'divider' },
              { key: 'exit', label: '退出登录' },
            ],
            onClick: ({ key }) => {
              if (key === 'exit') {
                clearSession()
                window.location.href = '/login'
              }
            },
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
              <div style={{
                width: 32, height: 32, borderRadius: '50%',
                background: portal === 'buyer' ? '#3E5BF2' : '#52c41a',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'white', fontSize: 13, fontWeight: 600
              }}>
                {portal === 'buyer' ? '张' : '贵'}
              </div>
            </div>
          </Dropdown>
        </div>
      </Header>

      <Sider
        width={220}
        style={{
          background: '#001529',
          position: 'fixed',
          height: '100vh',
          left: 0,
          top: 64,
          overflowY: 'auto'
        }}
      >
        <div style={{
          padding: '16px 16px 8px',
          color: 'rgba(255,255,255,0.65)',
          fontSize: 12,
          fontWeight: 600,
          letterSpacing: 1
        }}>
          {portal === 'buyer' ? '采 购 端' : '供 应 商 端'}
        </div>
        <Menu
          mode="inline"
          theme="dark"
          selectedKeys={[selectedKey]}
          items={menuItems}
          style={{ background: 'transparent', borderRight: 0 }}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      <AntLayout style={{ marginLeft: 220, marginTop: 64 }}>
        <Content style={{ padding: 20, minHeight: 'calc(100vh - 64px)' }}>
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  )
}

export default Layout
