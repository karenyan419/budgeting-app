import { test, expect } from '@playwright/test'
import { loginAs, seedTestData } from './helpers'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

test.describe('Upload', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page)
    await seedTestData(page)
    await page.goto('/')
    await page.waitForSelector('h1:has-text("Monthly Spending")')
  })

  test('upload CSV file shows success message', async ({ page }) => {
    // Switch to upload tab
    await page.locator('.tab', { hasText: 'Upload' }).click()

    // Should see upload form
    await expect(page.locator('.upload-form h2')).toHaveText('Upload Statement')

    // Upload test CSV
    const csvPath = path.resolve(__dirname, 'fixtures/monzo-test.csv')
    await page.locator('#csv-file').setInputFiles(csvPath)

    // Click the submit button inside the form
    await page.locator('.upload-form button[type="submit"]').click()

    // Should show success
    await expect(page.locator('.upload-result.success')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('.upload-result.success')).toContainText('imported')
  })

  test('upload form renders correctly', async ({ page }) => {
    await page.locator('.tab', { hasText: 'Upload' }).click()
    await expect(page.locator('.upload-form')).toBeVisible()
    await expect(page.locator('#account')).toBeVisible()
    await expect(page.locator('#csv-file')).toBeVisible()
  })
})
