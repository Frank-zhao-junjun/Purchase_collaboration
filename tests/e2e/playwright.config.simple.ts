import { defineConfig, devices } from '@playwright/test';

const CHROMIUM_PATH = '/root/.cache/ms-playwright/chromium-1161/chrome-linux/chrome';

export default defineConfig({
  testDir: './specs',
  workers: 1,
  reporter: [['list']],
  
  use: {
    baseURL: 'http://localhost:5000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    launchOptions: {
      executablePath: CHROMIUM_PATH,
    },
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
