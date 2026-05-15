import { useState, useEffect } from 'react'
import { authFetch } from '../auth'

function MonthlyReport({ selectedMonth, selectedYear, selectionKey }) {
  const now = new Date()
  const [month, setMonth] = useState(selectedMonth || now.getMonth() + 1)
  const [year, setYear] = useState(selectedYear || now.getFullYear())
  const [report, setReport] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showTransactions, setShowTransactions] = useState(false)
  const [edits, setEdits] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (selectedMonth && selectedYear) {
      setMonth(selectedMonth)
      setYear(selectedYear)
    }
  }, [selectedMonth, selectedYear, selectionKey])

  const fetchData = () => {
    setLoading(true)
    setError(null)
    Promise.all([
      authFetch(`/reports/monthly?month=${month}&year=${year}`).then(res => {
        if (!res.ok) throw new Error('Failed to load report')
        return res.json()
      }),
      authFetch(`/transactions/?month=${month}&year=${year}`).then(res => {
        if (!res.ok) throw new Error('Failed to load transactions')
        return res.json()
      }),
      authFetch('/categories/').then(res => res.json()),
    ])
      .then(([reportData, txData, catData]) => {
        setReport(reportData)
        setTransactions(txData)
        setCategories(catData)
        setEdits({})
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchData()
  }, [month, year])

  const handleEdit = (txId, field, value) => {
    setEdits(prev => ({
      ...prev,
      [txId]: { ...prev[txId], [field]: value },
    }))
  }

  const hasEdits = (txId) => {
    return edits[txId] !== undefined
  }

  const handleSaveAll = async () => {
    const ids = Object.keys(edits)
    if (ids.length === 0) return

    setSaving(true)
    try {
      await Promise.all(ids.map(id => {
        const changes = edits[id]
        const body = {}
        if ('category_id' in changes) {
          body.category_id = changes.category_id === '' ? null : Number(changes.category_id)
        }
        if ('excluded' in changes) {
          body.excluded = changes.excluded
        }
        return authFetch(`/transactions/${id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        }).then(res => {
          if (!res.ok) throw new Error(`Failed to save transaction ${id}`)
        })
      }))
      fetchData()
    } catch (err) {
      alert('Error saving: ' + err.message)
    } finally {
      setSaving(false)
    }
  }

  const handlePrevMonth = () => {
    if (month === 1) {
      setMonth(12)
      setYear(year - 1)
    } else {
      setMonth(month - 1)
    }
  }

  const handleNextMonth = () => {
    if (month === 12) {
      setMonth(1)
      setYear(year + 1)
    } else {
      setMonth(month + 1)
    }
  }

  const monthLabel = new Date(year, month - 1).toLocaleDateString('en-GB', {
    month: 'long',
    year: 'numeric',
  })

  const getCategoryValue = (tx) => {
    if (edits[tx.id] && 'category_id' in edits[tx.id]) {
      return edits[tx.id].category_id
    }
    return tx.category_id || ''
  }

  const getExcludedValue = (tx) => {
    if (edits[tx.id] && 'excluded' in edits[tx.id]) {
      return edits[tx.id].excluded
    }
    return tx.excluded
  }

  return (
    <div className="monthly-report">
      <div className="report-header">
        <h2>Monthly Budget</h2>
        <div className="month-nav">
          <button onClick={handlePrevMonth} aria-label="Previous month">&larr;</button>
          <span className="month-label">{monthLabel}</span>
          <button onClick={handleNextMonth} aria-label="Next month">&rarr;</button>
        </div>
      </div>

      {loading && <p className="status">Loading...</p>}
      {error && <p className="status error">Error: {error}</p>}

      {!loading && !error && report && (
        <>
          <div className="report-total">
            <span>Total spent</span>
            <span className="total-amount">&pound;{report.total_spent.toFixed(2)}</span>
          </div>

          <div className="category-list">
            {report.categories
              .filter(cat => cat.spent > 0 || (cat.budget && cat.budget > 0))
              .sort((a, b) => b.spent - a.spent)
              .map(cat => (
                <div key={cat.category_id} className={`category-row ${cat.over_budget ? 'over' : ''}`}>
                  <div className="category-info">
                    <span className="category-name">{cat.category_name}</span>
                    <span className="category-amounts">
                      &pound;{cat.spent.toFixed(2)}
                      {cat.budget ? ` / £${cat.budget.toFixed(2)}` : ''}
                    </span>
                  </div>
                  {cat.budget && cat.budget > 0 && (
                    <div className="budget-bar">
                      <div
                        className={`budget-fill ${cat.over_budget ? 'over' : ''}`}
                        style={{ width: `${Math.min(cat.percentage_used, 100)}%` }}
                      />
                      {cat.over_budget && (
                        <div
                          className="budget-overflow"
                          style={{ width: `${Math.min(cat.percentage_used - 100, 100)}%` }}
                        />
                      )}
                    </div>
                  )}
                  {cat.percentage_used !== null && (
                    <span className={`percentage ${cat.over_budget ? 'over' : ''}`}>
                      {cat.percentage_used.toFixed(0)}%
                    </span>
                  )}
                </div>
              ))}
          </div>

          {report.categories.every(cat => cat.spent === 0) && (
            <p className="status">No spending data for this month</p>
          )}

          <button
            className="toggle-transactions"
            onClick={() => setShowTransactions(!showTransactions)}
          >
            {showTransactions ? 'Hide' : 'Show'} Transactions ({transactions.length})
          </button>

          {showTransactions && transactions.length > 0 && (
            <div className={`transactions-table-wrapper ${Object.keys(edits).length > 0 ? 'has-unsaved' : ''}`}>
              <table className="transactions-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Amount</th>
                    <th>Category</th>
                    <th>Account</th>
                    <th>Excluded</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map(tx => (
                    <tr key={tx.id} className={`${getExcludedValue(tx) ? 'excluded-row' : ''} ${hasEdits(tx.id) ? 'edited-row' : ''}`}>
                      <td>{tx.date}</td>
                      <td className="tx-description">{tx.description}</td>
                      <td className={tx.amount < 0 ? 'amount-negative' : 'amount-positive'}>
                        {tx.amount < 0 ? '-' : '+'}£{Math.abs(tx.amount).toFixed(2)}
                      </td>
                      <td>
                        <select
                          className="tx-category-select"
                          value={getCategoryValue(tx)}
                          onChange={(e) => handleEdit(tx.id, 'category_id', e.target.value)}
                        >
                          <option value="">—</option>
                          {categories.map(cat => (
                            <option key={cat.id} value={cat.id}>{cat.name}</option>
                          ))}
                        </select>
                      </td>
                      <td>{tx.account_name || '—'}</td>
                      <td>
                        <input
                          type="checkbox"
                          checked={getExcludedValue(tx)}
                          onChange={(e) => handleEdit(tx.id, 'excluded', e.target.checked)}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {Object.keys(edits).length > 0 && (
                <div className="save-all-bar">
                  <span>{Object.keys(edits).length} unsaved change{Object.keys(edits).length > 1 ? 's' : ''}</span>
                  <button
                    className="save-button"
                    disabled={saving}
                    onClick={handleSaveAll}
                  >
                    {saving ? 'Saving...' : 'Save All'}
                  </button>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default MonthlyReport
