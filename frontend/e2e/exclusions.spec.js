import { test, expect } from '@playwright/test'
import { loginAs, seedTestData } from './helpers'

test.describe('Exclusion Rules', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page)
    await seedTestData(page)
    await page.goto('/')
    await page.waitForSelector('h1:has-text("Monthly Spending")')

    // Switch to exclusion rules tab
    await page.locator('.tab', { hasText: 'Exclusion Rules' }).click()
    await expect(page.locator('.exclusion-rules')).toBeVisible({ timeout: 5000 })
  })

  test('shows exclusion rules section', async ({ page }) => {
    await expect(page.locator('.exclusion-rules h2')).toHaveText('Exclusion Rules')
    await expect(page.locator('.exclusion-table')).toBeVisible()
  })

  test('add a new exclusion rule', async ({ page }) => {
    await page.locator('.add-rule-form input[type="text"]').first().fill('test pattern')
    await page.locator('.add-rule-form input[placeholder="Notes (optional)"]').fill('E2E test rule')
    await page.locator('.add-rule-form button[type="submit"]').click()

    await expect(page.locator('.exclusion-table')).toContainText('test pattern', { timeout: 5000 })
    await expect(page.locator('.exclusion-table')).toContainText('E2E test rule')
  })

  test('delete an exclusion rule', async ({ page }) => {
    // First add a rule
    await page.locator('.add-rule-form input[type="text"]').first().fill('delete me')
    await page.locator('.add-rule-form button[type="submit"]').click()
    await expect(page.locator('.exclusion-table')).toContainText('delete me', { timeout: 5000 })

    // Accept the confirm dialog
    page.on('dialog', dialog => dialog.accept())

    await page.locator('.delete-rule-button').last().click()
    await expect(page.locator('.exclusion-table')).not.toContainText('delete me', { timeout: 5000 })
  })

  test('apply rules button works', async ({ page }) => {
    await page.locator('.apply-rules-button').click()
    await expect(page.locator('.exclusion-message')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('.exclusion-message')).toContainText('Applied to')
  })
})
