import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * InventoryPage - 库存查询页面
 * 对应路由: /buyer/inventory
 */
export class InventoryPage extends BasePage {
  readonly path = '/buyer/inventory';

  // 页面元素
  readonly table = '.ant-table table';
  readonly tableRows = '.ant-table-tbody tr.ant-table-row';
  readonly searchInput = 'input[placeholder*="搜索"]';

  // 统计卡片
  readonly totalStockStat = '.ant-statistic:has-text("库存总量")';
  readonly stockValueStat = '.ant-statistic:has-text("库存价值")';
  readonly normalStat = '.ant-statistic:has-text("正常")';
  readonly warningStat = '.ant-statistic:has-text("预警")';

  // Tab按钮
  readonly rawMaterialTab = 'button:has-text("原料库存")';
  readonly finishedProductTab = 'button:has-text("成品库存")';

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

  async getInventoryCount(): Promise<number> {
    return await this.page.locator(this.tableRows).count();
  }

  async searchMaterials(keyword: string): Promise<void> {
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

  async getMaterialName(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(1)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getMaterialQuantity(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(3)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getMaterialStatus(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(7)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getMaterialCategory(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(2)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getMaterialUnitPrice(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(4)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getMaterialReorderPoint(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(5)`);
    return (await cell.textContent())?.trim() || '';
  }

  async getMaterialOrigin(row: number): Promise<string> {
    const cell = this.page.locator(`${this.tableRows}:nth-child(${row}) td:nth-child(6)`);
    return (await cell.textContent())?.trim() || '';
  }

  async filterByWarehouse(warehouse: string): Promise<void> {
    // 实际页面没有仓库筛选
  }

  async filterByCategory(category: string): Promise<void> {
    // 实际页面没有分类筛选
  }

  async filterByStockStatus(status: string): Promise<void> {
    // 实际页面没有库存状态筛选
  }

  async clickRawMaterialTab(): Promise<void> {
    const btn = this.page.locator(this.rawMaterialTab);
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await this.waitForLoading();
    }
  }

  async clickFinishedProductTab(): Promise<void> {
    const btn = this.page.locator(this.finishedProductTab);
    if (await btn.isVisible().catch(() => false)) {
      await btn.click();
      await this.waitForLoading();
    }
  }

  async clickInbound(): Promise<void> {
    // 实际页面没有入库按钮
  }

  async clickOutbound(): Promise<void> {
    // 实际页面没有出库按钮
  }

  async clickInventoryCheck(): Promise<void> {
    // 实际页面没有盘点按钮
  }

  async clickRefresh(): Promise<void> {
    await this.page.reload({ waitUntil: 'domcontentloaded' });
    await this.waitForLoading();
  }

  async clickExport(): Promise<void> {
    // 实际页面没有导出按钮
  }

  async getStats(): Promise<{ totalStock: number; stockValue: number; normal: number; warning: number }> {
    const getText = async (sel: string): Promise<number> => {
      const el = this.page.locator(sel);
      if (await el.isVisible().catch(() => false)) {
        const text = await el.textContent();
        const match = text?.match(/[\d,.]+/);
        return match ? parseFloat(match[0].replace(/,/g, '')) : 0;
      }
      return 0;
    };
    return {
      totalStock: await getText(this.totalStockStat),
      stockValue: await getText(this.stockValueStat),
      normal: await getText(this.normalStat),
      warning: await getText(this.warningStat),
    };
  }

  async getTotalRecords(): Promise<number> {
    const el = this.page.locator('.ant-pagination-total-text');
    if (await el.isVisible().catch(() => false)) {
      const text = await el.textContent();
      const match = text?.match(/\d+/);
      return match ? parseInt(match[0], 10) : 0;
    }
    return await this.getInventoryCount();
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
