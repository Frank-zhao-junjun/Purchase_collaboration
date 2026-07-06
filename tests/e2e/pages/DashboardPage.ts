import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * DashboardPage - 仪表盘页面 (采购端首页)
 * 对应路由: /buyer
 */
export class DashboardPage extends BasePage {
  readonly path = '/buyer';

  // 统计卡片
  readonly sourcingStatCard = '.ant-statistic:has-text("进行中寻源")';
  readonly contractStatCard = '.ant-statistic:has-text("待签署合同")';
  readonly supplierStatCard = '.ant-statistic:has-text("合格供应商")';

  // 快捷操作卡片
  readonly quickActionCards = '.ant-card-hoverable';
  readonly sourcingActionCard = '.ant-card-hoverable:has-text("发起寻源")';
  readonly contractActionCard = '.ant-card-hoverable:has-text("合同管理")';
  readonly orderActionCard = '.ant-card-hoverable:has-text("采购订单")';
  readonly supplierActionCard = '.ant-card-hoverable:has-text("供应商")';

  // 寻源项目列表
  readonly sourcingList = '.ant-list';
  readonly sourcingListItem = '.ant-list-item';

  // 导航菜单
  readonly navMenu = '.ant-menu';
  readonly dashboardNav = '.ant-menu-item:has-text("首页概览")';
  readonly purchaseOrderNav = '.ant-menu-item:has-text("采购订单")';
  readonly inventoryNav = '.ant-menu-item:has-text("库存查询")';

  constructor(page: Page) {
    super(page);
  }

  async visit(): Promise<void> {
    await this.navigate(this.path);
    await this.waitForLoading();
  }

  async waitForDashboardLoaded(): Promise<void> {
    // 等待快捷操作卡片或统计卡片出现
    await this.page.locator(this.quickActionCards).first().waitFor({ state: 'visible', timeout: 15000 });
  }

  async getSourcingCount(): Promise<number> {
    const card = this.page.locator(this.sourcingStatCard);
    if (await card.isVisible()) {
      const text = await card.textContent();
      const match = text?.match(/\d+/);
      return match ? parseInt(match[0], 10) : 0;
    }
    return 0;
  }

  async getContractCount(): Promise<number> {
    const card = this.page.locator(this.contractStatCard);
    if (await card.isVisible()) {
      const text = await card.textContent();
      const match = text?.match(/\d+/);
      return match ? parseInt(match[0], 10) : 0;
    }
    return 0;
  }

  async getSupplierCount(): Promise<number> {
    const card = this.page.locator(this.supplierStatCard);
    if (await card.isVisible()) {
      const text = await card.textContent();
      const match = text?.match(/\d+/);
      return match ? parseInt(match[0], 10) : 0;
    }
    return 0;
  }

  async getDashboardSummary(): Promise<{
    sourcingCount: number;
    contractCount: number;
    supplierCount: number;
  }> {
    return {
      sourcingCount: await this.getSourcingCount(),
      contractCount: await this.getContractCount(),
      supplierCount: await this.getSupplierCount(),
    };
  }

  async verifyMetricsLoaded(): Promise<void> {
    await expect(this.page.locator(this.quickActionCards).first()).toBeVisible();
  }

  async verifyQuickActions(): Promise<void> {
    await expect(this.page.locator(this.orderActionCard)).toBeVisible();
    await expect(this.page.locator(this.supplierActionCard)).toBeVisible();
  }

  async clickNewOrder(): Promise<void> {
    await this.page.locator(this.orderActionCard).click();
  }

  async goToPurchaseOrders(): Promise<void> {
    await this.page.locator(this.purchaseOrderNav).click();
  }

  async goToSuppliers(): Promise<void> {
    await this.page.locator(this.supplierActionCard).click();
  }

  async goToInventory(): Promise<void> {
    await this.page.locator(this.inventoryNav).click();
  }

  async refreshData(): Promise<void> {
    await this.page.reload({ waitUntil: 'domcontentloaded' });
    await this.waitForLoading();
  }

  async getAlerts(): Promise<string[]> {
    return [];
  }

  async getTodoItems(): Promise<string[]> {
    const items = await this.page.locator(this.sourcingListItem).all();
    const todos: string[] = [];
    for (const item of items) {
      const text = await item.textContent();
      if (text) todos.push(text.trim());
    }
    return todos;
  }
}
