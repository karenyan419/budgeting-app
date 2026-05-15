const API_URL = 'http://localhost:8001'

export const TEST_USER = { username: 'e2etest', password: 'e2epass123' }

/**
 * Register and login, storing the auth token.
 */
export async function loginAs(page, user = TEST_USER) {
  // Try register first (ignore if already exists)
  await page.request.post(`${API_URL}/auth/register`, {
    data: { username: user.username, password: user.password },
  }).catch(() => {})

  // Login via API to get token
  const res = await page.request.post(`${API_URL}/auth/login`, {
    data: { username: user.username, password: user.password },
  })
  const data = await res.json()
  const token = data.access_token

  // Set token in localStorage before navigating
  await page.goto('/')
  await page.evaluate((t) => localStorage.setItem('token', t), token)
  await page.goto('/')
  await page.waitForSelector('h1:has-text("Monthly Spending")', { timeout: 10000 })
}

/**
 * Seed test data via API: accounts, categories, and sample transactions.
 */
export async function seedTestData(page) {
  const token = await page.evaluate(() => localStorage.getItem('token'))
  const headers = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }

  // Clear database
  await page.request.post(`${API_URL}/admin/clear-database`, { headers })

  // Create accounts
  const monzoRes = await page.request.post(`${API_URL}/accounts/`, {
    headers,
    data: { name: 'Monzo', bank: 'monzo', type: 'current_account' },
  })
  const monzo = await monzoRes.json()

  // Create categories
  const catNames = [
    'Groceries', 'Eating Out', 'Transport', 'Shopping',
    'Entertainment', 'Bills', 'Health', 'Other', 'General',
  ]
  const cats = {}
  for (const name of catNames) {
    try {
      const res = await page.request.post(`${API_URL}/categories/`, {
        headers,
        data: { name, monthly_budget: 200 },
      })
      if (res.ok()) {
        const cat = await res.json()
        cats[name] = cat.id
      }
    } catch {
      // Retry once on connection error
      const res = await page.request.post(`${API_URL}/categories/`, {
        headers,
        data: { name, monthly_budget: 200 },
      })
      if (res.ok()) {
        const cat = await res.json()
        cats[name] = cat.id
      }
    }
  }

  return { monzoAccountId: monzo.id, categories: cats }
}

/**
 * Upload a CSV string as a file via the API.
 */
export async function uploadCSV(page, accountId, csvContent) {
  const token = await page.evaluate(() => localStorage.getItem('token'))

  await page.request.post(`${API_URL}/transactions/upload/${accountId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    multipart: {
      file: {
        name: 'test.csv',
        mimeType: 'text/csv',
        buffer: Buffer.from(csvContent),
      },
    },
  })
}

export const MONZO_CSV_HEADER = 'Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency,Local amount,Local currency,Notes and #tags,Address,Receipt,Description,Category split,Money Out,Money In'

export function monzoRow(id, isoDate, name, amount, category = 'General') {
  // Monzo parser expects DD/MM/YYYY format
  const [y, m, d] = isoDate.split('-')
  const date = `${d}/${m}/${y}`
  const moneyOut = amount < 0 ? Math.abs(amount).toFixed(2) : ''
  const moneyIn = amount > 0 ? amount.toFixed(2) : ''
  return `${id},${date},12:00:00,Card payment,${name},,${category},${amount.toFixed(2)},GBP,${Math.abs(amount).toFixed(2)},GBP,,,,,${moneyOut},${moneyIn}`
}
