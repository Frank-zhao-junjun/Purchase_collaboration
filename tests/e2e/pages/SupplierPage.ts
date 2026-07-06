import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * SupplierPage - 供应商列表页面
 * 对应路由: /buyer/suppliers
 */
export class SupplierPage extends BasePage {
  readonly path = '/buyer/suppliers';

  // 页面元素
  readonly table = '.ant-table table';
  readonly tableRows = '.ant-table-tbody tr.ant-table-row';
  readonly searchInput = 'input[placeholder*="搜索"]';
  readonly newButton = 'button:has-text("新增")';
  readonly exportButton = 'button:has-text("导出")';

  // 统计卡片
  readonly statCards = '.ant-statistic';
  readonly totalSuppliersStat = '.ant-statistic:has-text("供应商总数")';
  readonly activeSuppliersStat = '.ant-statistic:has-text("合作中")';
  readonly pendingSuppliersStat = '.ant-statistic:has-text("待审核")';
  readonly suspendedSuppliersStat = '.ant-statistic:has-text("已暂停")';

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

  async getSupplierCount(): Promise<number> {
    return await this.page.locator(this.tableRows).count();
  }

  async searchSuppliers(keyword: string): Promise<void> {
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

  async clickNewSupplier(): Promise<void> {
    const btn = this.page.locator(this.newButton).first();
    if (await btn.isVisible()) {
      await btn.click();
    }
  }

  async getSupplierName(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(1)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getSupplierStatus(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(7)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getSupplierRating(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(6)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getSupplierContact(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(2)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getSupplierPhone(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(3)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getSupplierEmail(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(4)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getSupplierAddress(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(5)`);
    return (await cell.textContent())?.trim() || '';
  }

  async clickViewSupplier(row: number): Promise<void> {
    const btn = this.page.locator(`${this.tableRows}:nth-child(${row}) button:has-text("查看")`);
    if (await btn.isVisible()) {
      await btn.click();
    }
  }

  async clickEditSupplier(row: number): Promise<void> {
    const btn = this.page.locator(`${this.tableRows}:nth-child(${row}) button:has-text("编辑")`);
    if (await btn.isVisible()) {
      await btn.click();
    }
  }

  async clickDeleteSupplier(row: number): Promise<void> {
    const btn = this.page.locator(`${this.tableRows}:nth-child(${row}) button:has-text("删除")`);
    if (await btn.isVisible()) {
      await btn.click();
    }
  }

  async clickConfirmDelete(): Promise<void> {
    const btn = this.page.locator('.ant-modal-confirm-btns button:has-text("确定")');
    if (await btn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await btn.click();
    }
  }

  async filterByStatus(status: string): Promise<void> {
    // 实际页面没有状态筛选下拉
  }

  async getStats(): Promise<{ total: number; active: number; pending: number; suspended: number }> {
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
      total: await getText(this.totalSuppliersStat),
      active: await getText(this.activeSuppliersStat),
      pending: await getText(this.pendingSuppliersStat),
      suspended: await getText(this.suspendedSuppliersStat),
    };
  }

  async getTotalRecords(): Promise<number> {
    const el = this.page.locator('.ant-pagination-total-text');
    if (await el.isVisible().catch(() => false)) {
      const text = await el.textContent();
      const match = text?.match(/\d+/);
      return match ? parseInt(match[0], 10) : 0;
    }
    return await this.getSupplierCount();
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
}
