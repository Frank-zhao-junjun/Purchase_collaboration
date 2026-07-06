import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * PurchaseOrderPage - 采购订单列表页面
 * 对应路由: /buyer/orders
 */
export class PurchaseOrderPage extends BasePage {
  readonly path = '/buyer/orders';

  // 页面元素
  readonly table = '.ant-table table';
  readonly tableRows = '.ant-table-tbody tr.ant-table-row';
  readonly searchInput = 'input[placeholder*="搜索"]';
  readonly newButton = 'button:has-text("新建")';
  readonly exportButton = 'button:has-text("导出")';

  // 统计卡片
  readonly totalOrdersStat = '.ant-statistic:has-text("订单总数")';
  readonly submittedOrdersStat = '.ant-statistic:has-text("已提交")';
  readonly confirmedOrdersStat = '.ant-statistic:has-text("已确认")';
  readonly shippedOrdersStat = '.ant-statistic:has-text("已发货")';
  readonly deliveredOrdersStat = '.ant-statistic:has-text("已到货")';
  readonly totalAmountStat = '.ant-statistic:has-text("总金额")';

  // 分页
  readonly pagination = '.ant-pagination';

  constructor(page: Page) {
    super(page);
  }

  async visit(): Promise<void> {
    await this.navigate(this.path);
    await this.waitForLoading();
  }

  async waitForListLoaded(): Promise<void> {
    await this.page.waitForSelector(this.table, { state: 'visible', timeout: 15000 });
    await this.page.waitForSelector(this.tableRows, { timeout: 10000 }).catch(() => {});
  }

  async getOrderCount(): Promise<number> {
    return await this.page.locator(this.tableRows).count();
  }

  async searchOrders(keyword: string): Promise<void> {
    const input = this.page.locator(this.searchInput);
    if (await input.isVisible()) {
      await input.fill(keyword);
      await this.page.waitForTimeout(500);
    }
  }

  async clearSearch(): Promise<void> {
    const input = this.page.locator(this.searchInput);
    if (await input.isVisible()) {
      await input.fill('');
      await this.page.waitForTimeout(500);
    }
  }

  async clickNewOrder(): Promise<void> {
    const btn = this.page.locator(this.newButton).first();
    if (await btn.isVisible()) {
      await btn.click();
    }
  }

  async getOrderNumber(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(1)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getOrderStatus(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(5)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getOrderAmount(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(3)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getOrderDate(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(4)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getOrderType(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(2)`);
    return (await cell.textContent())?.trim() || '';
  }

  async clickViewOrder(row: number): Promise<void> {
    const btn = this.page.locator(`${this.tableRows}:nth-child(${row}) button:has-text("查看")`);
    if (await btn.isVisible()) {
      await btn.click();
    }
  }

  async clickConfirmOrder(row: number): Promise<void> {
    const btn = this.page.locator(`${this.tableRows}:nth-child(${row}) button:has-text("确认")`);
    if (await btn.isVisible()) {
      await btn.click();
    }
  }

  async clickDispatchOrder(row: number): Promise<void> {
    const btn = this.page.locator(`${this.tableRows}:nth-child(${row}) button:has-text("发货")`);
    if (await btn.isVisible()) {
      await btn.click();
    }
  }

  async clickConfirmDispatch(): Promise<void> {
    const btn = this.page.locator('.ant-modal button:has-text("确定")');
    if (await btn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await btn.click();
    }
  }

  async filterByStatus(status: string): Promise<void> {
    // 实际页面没有状态筛选下拉
  }

  async getStats(): Promise<{ total: number; submitted: number; confirmed: number; shipped: number; delivered: number }> {
    const getText = async (sel: string): Promise<number> => {
      const el = this.page.locator(sel);
      if (await el.isVisible().catch(() => false)) {
        const text = await el.textContent();
        const match = text?.match(/\d+/);
        return match ? parseInt(match[0], 10) : 0;
      }
      return 0;
    };
    return {
      total: await getText(this.totalOrdersStat),
      submitted: await getText(this.submittedOrdersStat),
      confirmed: await getText(this.confirmedOrdersStat),
      shipped: await getText(this.shippedOrdersStat),
      delivered: await getText(this.deliveredOrdersStat),
    };
  }

  async getTotalRecords(): Promise<number> {
    const el = this.page.locator('.ant-pagination-total-text');
    if (await el.isVisible().catch(() => false)) {
      const text = await el.textContent();
      const match = text?.match(/\d+/);
      return match ? parseInt(match[0], 10) : 0;
    }
    return await this.getOrderCount();
  }

  async goToNextPage(): Promise<void> {
    const btn = this.page.locator('.ant-pagination-next:not(.ant-pagination-disabled)');
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await this.waitForLoading();
    }
  }

  async goToPrevPage(): Promise<void> {
    const btn = this.page.locator('.ant-pagination-prev:not(.ant-pagination-disabled)');
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await this.waitForLoading();
    }
  }

  async goToPage(pageNum: number): Promise<void> {
    const btn = this.page.locator(`.ant-pagination-item-${pageNum}:not(.ant-pagination-item-active)`);
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await this.waitForLoading();
    }
  }

  async clickExport(): Promise<void> {
    const btn = this.page.locator(this.exportButton);
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
    }
  }
}
