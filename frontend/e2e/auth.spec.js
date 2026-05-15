import { test, expect } from '@playwright/test'

const uniqueUser = () => ({
  username: `user_${Date.now()}`,
  password: 'testpass123',
})

test.describe('Authentication', () => {
  test('register, logout, and login again', async ({ page }) => {
    const user = uniqueUser()
    await page.goto('/')

    // Should see login page
    await expect(page.locator('h2')).toHaveText('Sign In')

    // Switch to register
    await page.locator('.link-button').click()
    await expect(page.locator('h2')).toHaveText('Create Account')

    // Register
    await page.getByLabel('Username').fill(user.username)
    await page.getByLabel('Password').fill(user.password)
    await page.locator('button[type="submit"]').click()

    // Should see dashboard
    await expect(page.locator('h1')).toHaveText('Monthly Spending', { timeout: 10000 })

    // Logout
    await page.getByRole('button', { name: 'Sign Out' }).click()
    await expect(page.locator('h2')).toHaveText('Sign In')

    // Login again
    await page.getByLabel('Username').fill(user.username)
    await page.getByLabel('Password').fill(user.password)
    await page.locator('button[type="submit"]').click()

    await expect(page.locator('h1')).toHaveText('Monthly Spending', { timeout: 10000 })
  })

  test('shows error for wrong password', async ({ page }) => {
    await page.goto('/')
    await page.getByLabel('Username').fill('nonexistent_user')
    await page.getByLabel('Password').fill('wrongpass')
    await page.locator('button[type="submit"]').click()

    await expect(page.locator('.login-error')).toBeVisible({ timeout: 5000 })
  })
})
