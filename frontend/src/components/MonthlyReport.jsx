import { useState, useEffect } from 'react'
import { authFetch } from '../auth'

function MonthlyReport({ selectedMonth, selectedYear }) {
  const now = new Date()
  const [month, setMonth] = useState(selectedMonth || now.getMonth() + 1)
  const [year, setYear] = useState(selectedYear || now.getFullYear())
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (selectedMonth && selectedYear) {
      setMonth(selectedMonth)
      setYear(selectedYear)
    }
  }, [selectedMonth, selectedYear])

  useEffect(() => {
    setLoading(true)
    setError(null)
    authFetch(`/reports/monthly?month=${month}&year=${year}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load report')
        return res.json()
      })
      .then(data => setReport(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [month, year])

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
        </>
      )}
    </div>
  )
}

export default MonthlyReport
