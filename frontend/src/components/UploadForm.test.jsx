import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import UploadForm from './UploadForm'

const mockAccounts = [
  { id: 1, name: 'Monzo', bank: 'monzo', type: 'current_account' },
  { id: 2, name: 'Yonder', bank: 'yonder', type: 'credit_card' },
]

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('UploadForm', () => {
  it('loads and displays accounts', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockAccounts),
    })
    render(<UploadForm />)
    await waitFor(() => {
      expect(screen.getByText('Monzo')).toBeInTheDocument()
      expect(screen.getByText('Yonder')).toBeInTheDocument()
    })
  })

  it('shows error when accounts fail to load', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Network error'))
    render(<UploadForm />)
    await waitFor(() => {
      expect(screen.getByText('Failed to load accounts')).toBeInTheDocument()
    })
  })

  it('disables button when no file selected', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockAccounts),
    })
    render(<UploadForm />)
    await waitFor(() => {
      expect(screen.getByText('Monzo')).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: 'Upload' })).toBeDisabled()
  })

  it('uploads file and shows success', async () => {
    const onSuccess = vi.fn()
    const uploadResponse = { message: 'Imported 5 transactions', imported: 5, skipped: 1 }

    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      if (url.includes('/accounts/')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAccounts) })
      }
      if (url.includes('/transactions/upload/')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(uploadResponse) })
      }
    })

    render(<UploadForm onUploadSuccess={onSuccess} />)
    await waitFor(() => {
      expect(screen.getByText('Monzo')).toBeInTheDocument()
    })

    const fileInput = screen.getByLabelText('CSV file')
    const file = new File(['date,amount\n2026-01-01,50'], 'test.csv', { type: 'text/csv' })
    fireEvent.change(fileInput, { target: { files: [file] } })

    fireEvent.click(screen.getByRole('button', { name: 'Upload' }))

    await waitFor(() => {
      expect(screen.getByText('Imported 5 transactions')).toBeInTheDocument()
      expect(screen.getByText('5 imported, 1 duplicates skipped')).toBeInTheDocument()
    })
    expect(onSuccess).toHaveBeenCalled()
  })

  it('shows error on upload failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockImplementation((url) => {
      if (url.includes('/accounts/')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAccounts) })
      }
      if (url.includes('/transactions/upload/')) {
        return Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: 'Invalid CSV format' }),
        })
      }
    })

    render(<UploadForm />)
    await waitFor(() => {
      expect(screen.getByText('Monzo')).toBeInTheDocument()
    })

    const fileInput = screen.getByLabelText('CSV file')
    const file = new File(['bad data'], 'test.csv', { type: 'text/csv' })
    fireEvent.change(fileInput, { target: { files: [file] } })

    fireEvent.click(screen.getByRole('button', { name: 'Upload' }))

    await waitFor(() => {
      expect(screen.getByText('Invalid CSV format')).toBeInTheDocument()
    })
  })
})
