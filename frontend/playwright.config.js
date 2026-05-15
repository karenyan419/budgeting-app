import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 1,
  workers: 1,
  fullyParallel: false,
  use: {
    baseURL: 'http://localhost:5174',
    headless: true,
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
  webServer: [
    {
      command: 'cd ../backend && source venv/bin/activate && DATABASE_URL=sqlite:///./test_e2e.db CORS_ORIGINS=http://localhost:5174 uvicorn main:app --port 8001',
      port: 8001,
      reuseExistingServer: false,
      timeout: 15000,
    },
    {
      command: 'VITE_API_URL=http://localhost:8001 npx vite --port 5174',
      port: 5174,
      reuseExistingServer: false,
      timeout: 15000,
    },
  ],
})
