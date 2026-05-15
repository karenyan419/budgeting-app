import { test, expect } from '@playwright/test'
import { loginAs, seedTestData, uploadCSV, MONZO_CSV_HEADER, monzoRow } from './helpers'

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page)
    const { monzoAccountId } = await seedTestData(page)

    // Upload test data for current month
    const now = new Date()
    const y = now.getFullYear()
    const m = String(now.getMonth() + 1).padStart(2, '0')
    const csv = [
      MONZO_CSV_HEADER,
      monzoRow('dash_001', `${y}-${m}-01`, 'Tesco', -50, 'Groceries'),
      monzoRow('dash_002', `${y}-${m}-02`, 'Uber', -15, 'Transport'),
      monzoRow('dash_003', `${y}-${m}-03`, 'Cinema', -20, 'Entertainment'),
    ].join('\n')
    await uploadCSV(page, monzoAccountId, csv)

    await page.goto('/')
    await page.waitForSelector('h1:has-text("Monthly Spending")')
  })

  test('chart renders with data', async ({ page }) => {
    await expect(page.locator('.recharts-responsive-container')).toBeVisible({ timeout: 10000 })
    // Recharts renders bars as path.recharts-rectangle
    await expect(page.locator('.recharts-rectangle').first()).toBeVisible({ timeout: 10000 })
  })

  test('month selector changes data range', async ({ page }) => {
    await expect(page.locator('.recharts-responsive-container')).toBeVisible({ timeout: 10000 })
    await page.selectOption('#months', '3')
    await expect(page.locator('.recharts-responsive-container')).toBeVisible()
  })

  test('stack mode selector works', async ({ page }) => {
    // Wait for chart to have data
    await expect(page.locator('.recharts-responsive-container')).toBeVisible({ timeout: 10000 })
    await page.waitForTimeout(1000)

    await page.selectOption('#stack-mode', 'account')
    // Legend appears in stacked mode
    await expect(page.locator('.recharts-default-legend')).toBeVisible({ timeout: 5000 })

    await page.selectOption('#stack-mode', 'category')
    await expect(page.locator('.recharts-default-legend')).toBeVisible({ timeout: 5000 })
  })
})
