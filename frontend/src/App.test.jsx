import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from './App'

// Mock recharts to avoid canvas/SVG issues in jsdom
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>,
  BarChart: ({ children }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  ReferenceLine: () => <div />,
}))

const mockTrendsData = [
  { year: 2026, month: 1, total_spent: 450.00 },
  { year: 2026, month: 2, total_spent: 320.50 },
  { year: 2026, month: 3, total_spent: 510.75 },
]

const mockAccounts = [
  { id: 1, name: 'Monzo', bank: 'monzo', type: 'current_account' },
  { id: 2, name: 'Yonder', bank: 'yonder', type: 'credit_card' },
]

beforeEach(() => {
  vi.restoreAllMocks()
})

function mockFetch(handlers) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
    for (const [pattern, response] of Object.entries(handlers)) {
      if (url.includes(pattern)) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(response),
        })
      }
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) })
  })
}

describe('App', () => {
  it('shows loading state initially', () => {
    mockFetch({ '/reports/trends': [], '/accounts/': mockAccounts })
    render(<App />)
    expect(screen.getAllByText('Loading...').length).toBeGreaterThan(0)
  })

  it('renders chart when data loads', async () => {
    mockFetch({ '/reports/trends': mockTrendsData, '/accounts/': mockAccounts })
    render(<App />)
    await waitFor(() => {
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    })
  })

  it('shows error when fetch fails', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      if (url.includes('/accounts/')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAccounts) })
      }
      return Promise.resolve({ ok: false })
    })
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch spending data/)).toBeInTheDocument()
    })
  })

  it('shows no data message when empty', async () => {
    mockFetch({ '/reports/trends': [], '/accounts/': mockAccounts })
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('No spending data available')).toBeInTheDocument()
    })
  })

  it('changes months when selector changes', async () => {
    const fetchSpy = mockFetch({ '/reports/trends': mockTrendsData, '/accounts/': mockAccounts })
    render(<App />)
    await waitFor(() => {
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
    })

    fireEvent.change(screen.getByLabelText('Show last:'), { target: { value: '12' } })

    await waitFor(() => {
      const trendsCalls = fetchSpy.mock.calls.filter(c => c[0].includes('/reports/trends'))
      const lastCall = trendsCalls[trendsCalls.length - 1][0]
      expect(lastCall).toContain('months=12')
    })
  })

  it('renders the upload form', async () => {
    mockFetch({ '/reports/trends': mockTrendsData, '/accounts/': mockAccounts })
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Upload Statement')).toBeInTheDocument()
    })
  })
})
