import { useState, useEffect } from 'react'
import { authFetch, authHeaders } from '../auth'

function UploadForm({ onUploadSuccess }) {
  const [accounts, setAccounts] = useState([])
  const [selectedAccount, setSelectedAccount] = useState('')
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [latestDates, setLatestDates] = useState({})

  useEffect(() => {
    authFetch('/accounts/')
      .then(res => res.json())
      .then(data => {
        setAccounts(data)
        if (data.length > 0) setSelectedAccount(data[0].id)
      })
      .catch(() => setError('Failed to load accounts'))

    authFetch('/transactions/latest-dates')
      .then(res => res.json())
      .then(data => setLatestDates(data))
      .catch(() => {})
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file || !selectedAccount) return

    setUploading(true)
    setResult(null)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await authFetch(
        `/transactions/upload/${selectedAccount}`,
        { method: 'POST', body: formData }
      )

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Upload failed')
      }

      const data = await response.json()
      setResult(data)
      setFile(null)
      // Reset the file input
      e.target.reset()
      if (onUploadSuccess) onUploadSuccess()
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="upload-form">
      <h2>Upload Statement</h2>

      {Object.keys(latestDates).length > 0 && (
        <div className="latest-dates">
          <p><strong>Most recent transactions:</strong></p>
          {Object.entries(latestDates).map(([name, date]) => (
            <p key={name}>{name}: {date || 'No transactions yet'}</p>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <label htmlFor="account">Account</label>
          <select
            id="account"
            value={selectedAccount}
            onChange={(e) => setSelectedAccount(Number(e.target.value))}
          >
            {accounts.map(acc => (
              <option key={acc.id} value={acc.id}>
                {acc.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-row">
          <label htmlFor="csv-file">CSV file</label>
          <input
            id="csv-file"
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files[0])}
          />
        </div>

        <button type="submit" disabled={uploading || !file}>
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </form>

      {result && (
        <div className="upload-result success">
          <p>{result.message}</p>
          <p className="upload-details">
            {result.imported} imported, {result.skipped} duplicates skipped
          </p>
        </div>
      )}

      {error && (
        <div className="upload-result error">
          <p>{error}</p>
        </div>
      )}
    </div>
  )
}

export default UploadForm
