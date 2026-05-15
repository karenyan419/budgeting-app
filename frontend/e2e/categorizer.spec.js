import { test, expect } from '@playwright/test'
import { loginAs, seedTestData, uploadCSV, MONZO_CSV_HEADER, monzoRow } from './helpers'

test.describe('Categorizer', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page)
    const { monzoAccountId } = await seedTestData(page)

    const now = new Date()
    const y = now.getFullYear()
    const m = String(now.getMonth() + 1).padStart(2, '0')
    const csv = [
      MONZO_CSV_HEADER,
      monzoRow('cat_001', `${y}-${m}-01`, 'Mystery Shop', -25, 'General'),
      monzoRow('cat_002', `${y}-${m}-02`, 'Unknown Store', -30, 'General'),
      monzoRow('cat_003', `${y}-${m}-03`, 'Random Place', -15, 'General'),
    ].join('\n')
    await uploadCSV(page, monzoAccountId, csv)

    await page.goto('/')
    await page.waitForSelector('h1:has-text("Monthly Spending")')

    // Switch to categorize tab
    await page.locator('.tab', { hasText: 'Categorize' }).click()
  })

  test('shows transaction card with category buttons', async ({ page }) => {
    await expect(page.locator('.cat-card')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('.cat-description')).toBeVisible()
    await expect(page.locator('.cat-amount')).toBeVisible()
    await expect(page.locator('.cat-choice').first()).toBeVisible()
    await expect(page.locator('.cat-key').first()).toBeVisible()
  })

  test('keyboard shortcut categorizes transaction', async ({ page }) => {
    await expect(page.locator('.cat-card')).toBeVisible({ timeout: 10000 })

    // Press "1" to categorize as first category
    await page.keyboard.press('1')
    await page.waitForTimeout(500)

    await expect(page.locator('.cat-score')).toContainText('1 done')
  })

  test('skip moves to next card', async ({ page }) => {
    await expect(page.locator('.cat-card')).toBeVisible({ timeout: 10000 })

    await page.keyboard.press('s')
    await page.waitForTimeout(300)

    // Score should still be 0
    await expect(page.locator('.cat-score')).toContainText('0 done')
    // Should still show a card (there are more transactions)
    await expect(page.locator('.cat-card')).toBeVisible()
  })

  test('undo reverts last categorization', async ({ page }) => {
    await expect(page.locator('.cat-card')).toBeVisible({ timeout: 10000 })

    await page.keyboard.press('1')
    await page.waitForTimeout(500)
    await expect(page.locator('.cat-score')).toContainText('1 done')

    await page.keyboard.press('u')
    await page.waitForTimeout(500)
    await expect(page.locator('.cat-score')).toContainText('0 done')
  })

  test('clicking category button works', async ({ page }) => {
    await expect(page.locator('.cat-card')).toBeVisible({ timeout: 10000 })

    await page.locator('.cat-choice').first().click()
    await page.waitForTimeout(500)

    await expect(page.locator('.cat-score')).toContainText('1 done')
  })
})
