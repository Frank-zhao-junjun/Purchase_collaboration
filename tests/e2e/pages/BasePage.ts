import { Page, Locator, expect } from '@playwright/test';

/**
 * BasePage - 基础页面类
 * 封装常用操作：导航、点击、填写、等待
 */
export class BasePage {
  protected page: Page;
  protected baseURL: string;

  constructor(page: Page, baseURL: string = 'http://localhost:5000') {
    this.page = page;
    this.baseURL = baseURL;
  }

  /**
   * 导航到指定页面
   */
  async navigate(path: string): Promise<void> {
    await this.page.goto(new URL(path, this.baseURL).toString(), {
      waitUntil: 'domcontentloaded'
    });
  }

  /**
   * 点击元素
   */
  async click(selector: string, options?: { force?: boolean; timeout?: number }): Promise<void> {
    await this.page.click(selector, { timeout: options?.timeout ?? 10000, ...options });
  }

  /**
   * 双击元素
   */
  async doubleClick(selector: string): Promise<void> {
    await this.page.dblclick(selector);
  }

  /**
   * 填写输入框
   */
  async fill(selector: string, value: string): Promise<void> {
    await this.page.fill(selector, value);
  }

  /**
   * 清空并填写输入框
   */
  async clearAndFill(selector: string, value: string): Promise<void> {
    await this.page.click(selector, { clickCount: 3 });
    await this.page.fill(selector, value);
  }

  /**
   * 等待元素可见
   */
  async waitForVisible(selector: string, timeout: number = 10000): Promise<Locator> {
    const locator = this.page.locator(selector);
    await locator.waitFor({ state: 'visible', timeout });
    return locator;
  }

  /**
   * 等待元素隐藏
   */
  async waitForHidden(selector: string, timeout: number = 10000): Promise<void> {
    await this.page.locator(selector).waitFor({ state: 'hidden', timeout });
  }

  /**
   * 等待元素出现并返回文本
   */
  async getText(selector: string, timeout: number = 10000): Promise<string> {
    const locator = this.page.locator(selector);
    await locator.waitFor({ state: 'visible', timeout });
    return locator.textContent() ?? '';
  }

  /**
   * 获取元素数量
   */
  async getCount(selector: string): Promise<number> {
    return this.page.locator(selector).count();
  }

  /**
   * 等待URL包含指定路径
   */
  async waitForURL(pattern: string | RegExp, timeout: number = 30000): Promise<void> {
    await this.page.waitForURL(pattern, { timeout });
  }

  /**
   * 等待网络空闲
   */
  async waitForNetworkIdle(timeout: number = 30000): Promise<void> {
    await this.page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * 截图
   */
  async screenshot(options?: { path?: string; fullPage?: boolean }): Promise<Buffer> {
    return this.page.screenshot(options);
  }

  /**
   * 滚动到元素
   */
  async scrollToElement(selector: string): Promise<void> {
    await this.page.locator(selector).scrollIntoViewIfNeeded();
  }

  /**
   * 悬停
   */
  async hover(selector: string): Promise<void> {
    await this.page.hover(selector);
  }

  /**
   * 等待下拉选项
   */
  async selectOption(selector: string, value: string | string[]): Promise<void> {
    await this.page.selectOption(selector, value);
  }

  /**
   * 检查元素是否存在
   */
  async isVisible(selector: string): Promise<boolean> {
    return this.page.locator(selector).isVisible();
  }

  /**
   * 检查元素是否被选中
   */
  async isChecked(selector: string): Promise<boolean> {
    return this.page.locator(selector).isChecked();
  }

  /**
   * 等待表格加载完成
   */
  async waitForTableLoad(tableSelector: string = 'table'): Promise<void> {
    await this.page.waitForSelector(`${tableSelector} tbody tr`, { timeout: 10000 });
  }

  /**
   * 获取表格行数
   */
  async getTableRowCount(tableSelector: string = 'table'): Promise<number> {
    const rows = await this.page.locator(`${tableSelector} tbody tr`).all();
    return rows.length;
  }

  /**
   * 通用断言：元素文本包含期望值
   */
  async expectTextContains(selector: string, expectedText: string): Promise<void> {
    const locator = this.page.locator(selector);
    await expect(locator).toContainText(expectedText);
  }

  /**
   * 通用断言：元素存在
   */
  async expectExists(selector: string): Promise<void> {
    await expect(this.page.locator(selector)).toBeAttached();
  }

  /**
   * 通用断言：元素可见
   */
  async expectVisible(selector: string): Promise<void> {
    await expect(this.page.locator(selector)).toBeVisible();
  }

  /**
   * 通用断言：元素可点击
   */
  async expectEnabled(selector: string): Promise<void> {
    await expect(this.page.locator(selector)).toBeEnabled();
  }

  /**
   * 关闭当前弹窗/对话框
   */
  async closeModal(): Promise<void> {
    const closeButton = this.page.locator('.ant-modal-close, .ant-drawer-close, [class*="close"]').first();
    if (await closeButton.isVisible()) {
      await closeButton.click();
    }
  }

  /**
   * 等待loading消失
   */
  async waitForLoading(timeout: number = 30000): Promise<void> {
    try {
      await this.page.waitForSelector('.ant-spin-spinning', { state: 'hidden', timeout: 5000 });
    } catch {
      // loading可能不存在，忽略
    }
  }

  /**
   * 刷新页面
   */
  async refresh(): Promise<void> {
    await this.page.reload({ waitUntil: 'networkidle' });
  }

  /**
   * 返回上一页
   */
  async goBack(): Promise<void> {
    await this.page.goBack();
  }

  /**
   * 按键盘按键
   */
  async pressKey(selector: string, key: string): Promise<void> {
    await this.page.locator(selector).press(key);
  }

  /**
   * 拖拽元素
   */
  async dragAndDrop(fromSelector: string, toSelector: string): Promise<void> {
    await this.page.locator(fromSelector).dragTo(this.page.locator(toSelector));
  }

  /**
   * 获取当前URL
   */
  async getCurrentURL(): Promise<string> {
    return this.page.url();
  }

  /**
   * 获取表格单元格文本
   */
  async getCellText(rowIndex: number, colIndex: number, tableSelector: string = 'table'): Promise<string> {
    const cell = this.page.locator(`${tableSelector} tbody tr:nth-child(${rowIndex}) td:nth-child(${colIndex})`);
    await cell.waitFor({ state: 'visible' });
    return cell.textContent() ?? '';
  }
}
