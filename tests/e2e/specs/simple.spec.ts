import { test, expect } from '@playwright/test';

test.describe('简单冒烟测试', () => {
  test('首页可以访问', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/采购供应链/);
  });

  test('API健康检查', async ({ page }) => {
    const response = await page.request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
  });

  test('Dashboard数据加载', async ({ page }) => {
    await page.goto('/');
    // 等待页面加载
    await page.waitForTimeout(2000);
    // 截图保存
    await page.screenshot({ path: 'test-results/dashboard.png' });
  });
});
