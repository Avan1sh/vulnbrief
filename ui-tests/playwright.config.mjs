import {defineConfig} from '@playwright/test';
import {fileURLToPath} from 'node:url';

export default defineConfig({
  testDir: '.',
  testMatch: '*.spec.mjs',
  fullyParallel: false,
  workers: 1,
  timeout: 30000,
  retries: 0,
  webServer: {
    command: 'python -m vulnbrief serve --port 8788 --data .vulnbrief/browser-tests',
    cwd: fileURLToPath(new URL('..',import.meta.url)),
    url: 'http://127.0.0.1:8788/api/config',
    reuseExistingServer: !process.env.CI,
    timeout: 30000
  },
  reporter: [['list'], ['json', {outputFile: '../artifacts/browser-tests.json'}]],
  use: {
    baseURL: process.env.VULNBRIEF_TEST_URL || 'http://127.0.0.1:8788',
    viewport: {width: 1440, height: 1000},
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    reducedMotion: 'reduce'
  }
});
