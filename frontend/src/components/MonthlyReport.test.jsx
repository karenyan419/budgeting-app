import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import MonthlyReport from './MonthlyReport'

const mockReport = {
  month: 4,
  year: 2026,
  total_spent: 875.50,
  categories: [
    { category_id: 1, category_name: 'Transport', spent: 180.00, budget: 150.00, percentage_used: 120.0, over_budget: true },
    { category_id: 2, category_name: 'Groceries', spent: 350.25, budget: 400.00, percentage_used: 87.6, over_budget: false },
    { category_id: 3, category_name: 'Eating Out', spent: 195.25, budget: 200.00, percentage_used: 97.6, over_budget: false },
    { category_id: 4, category_name: 'Entertainment', spent: 0, budget: 100.00, percentage_used: 0, over_budget: false },
    { category_id: 5, category_name: 'Shopping', spent: 150.00, budget: 150.00, percentage_used: 100.0, over_budget: false },
  ],
}

beforeEach(() => {
  vi.restoreAllMocks()
})

function mockFetchReport(report) {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(report),
  })
}

describe('MonthlyReport', () => {
  it('shows loading state', () => {
    mockFetchReport(mockReport)
    render(<MonthlyReport />)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('renders report with total and categories', async () => {
    mockFetchReport(mockReport)
    render(<MonthlyReport />)
    await waitFor(() => {
      expect(screen.getByText('£875.50')).toBeInTheDocument()
      expect(screen.getByText('Groceries')).toBeInTheDocument()
      expect(screen.getByText('Transport')).toBeInTheDocument()
    })
  })

  it('highlights over-budget categories', async () => {
    mockFetchReport(mockReport)
    render(<MonthlyReport />)
    await waitFor(() => {
      expect(screen.getByText('120%')).toBeInTheDocument()
    })
  })

  it('hides categories with no spend and no budget', async () => {
    const report = {
      ...mockReport,
      categories: [
        ...mockReport.categories,
        { category_id: 99, category_name: 'Empty', spent: 0, budget: null, percentage_used: null, over_budget: false },
      ],
    }
    mockFetchReport(report)
    render(<MonthlyReport />)
    await waitFor(() => {
      expect(screen.getByText('Groceries')).toBeInTheDocument()
    })
    expect(screen.queryByText('Empty')).not.toBeInTheDocument()
  })

  it('navigates months', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockReport),
    })
    render(<MonthlyReport />)
    await waitFor(() => {
      expect(screen.getByText('£875.50')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByLabelText('Previous month'))
    await waitFor(() => {
      const calls = fetchSpy.mock.calls.map(c => c[0])
      expect(calls.some(url => url.includes('month=3'))).toBe(true)
    })
  })

  it('shows error on fetch failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: false })
    render(<MonthlyReport />)
    await waitFor(() => {
      expect(screen.getByText(/Failed to load report/)).toBeInTheDocument()
    })
  })
})
