import { test, expect } from '@playwright/test'
import { loginAs, seedTestData, uploadCSV, MONZO_CSV_HEADER, monzoRow } from './helpers'

test.describe('Monthly Report', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page)
    const { monzoAccountId } = await seedTestData(page)

    const now = new Date()
    const y = now.getFullYear()
    const m = String(now.getMonth() + 1).padStart(2, '0')
    const csv = [
      MONZO_CSV_HEADER,
      monzoRow('rpt_001', `${y}-${m}-01`, 'Tesco', -50, 'Groceries'),
      monzoRow('rpt_002', `${y}-${m}-02`, 'Nandos', -30, 'Eating Out'),
    ].join('\n')
    await uploadCSV(page, monzoAccountId, csv)

    await page.goto('/')
    await page.waitForSelector('.monthly-report', { timeout: 10000 })
  })

  test('report loads with current month', async ({ page }) => {
    await expect(page.locator('.month-label')).toContainText('2026')
    await expect(page.locator('.total-amount')).toBeVisible()
  })

  test('month navigation works', async ({ page }) => {
    const initialMonth = await page.locator('.month-label').textContent()

    await page.getByLabel('Previous month').click()
    const prevMonth = await page.locator('.month-label').textContent()
    expect(prevMonth).not.toBe(initialMonth)

    await page.getByLabel('Next month').click()
    const backToOriginal = await page.locator('.month-label').textContent()
    expect(backToOriginal).toBe(initialMonth)
  })

  test('show transactions toggle reveals table', async ({ page }) => {
    await expect(page.locator('.transactions-table')).not.toBeVisible()

    // Button text includes count, use partial match
    await page.locator('.toggle-transactions').click()

    await expect(page.locator('.transactions-table')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.transactions-table th').first()).toHaveText('Date')
  })

  test('transaction table has editable controls', async ({ page }) => {
    await page.locator('.toggle-transactions').click()
    await expect(page.locator('.transactions-table')).toBeVisible({ timeout: 5000 })

    // Category dropdown
    await expect(page.locator('.tx-category-select').first()).toBeVisible()

    // Excluded checkbox
    await expect(page.locator('.transactions-table input[type="checkbox"]').first()).toBeVisible()
  })
})
