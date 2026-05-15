import { useState, useEffect, useRef } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer
} from 'recharts'
import UploadForm from './components/UploadForm'
import MonthlyReport from './components/MonthlyReport'
import ExclusionRules from './components/ExclusionRules'
import Categorizer from './components/Categorizer'
import Login from './components/Login'
import { isAuthenticated, clearToken, authFetch } from './auth'
import './App.css'

function App() {
  const [loggedIn, setLoggedIn] = useState(isAuthenticated())
  // State for storing spending data from API
  const [spendingData, setSpendingData] = useState([])
  // State for how many months to show (default: 6)
  const [monthsToShow, setMonthsToShow] = useState(6)
  // State for chart stacking mode: 'total', 'account', 'category'
  const [stackMode, setStackMode] = useState('total')
  // State for loading indicator
  const [loading, setLoading] = useState(true)
  // State for error messages
  const [error, setError] = useState(null)
  // State for selected month from chart click
  const [selectedMonth, setSelectedMonth] = useState(null)
  const [selectedYear, setSelectedYear] = useState(null)
  const [selectionKey, setSelectionKey] = useState(0)
  const reportRef = useRef(null)
  const [clearing, setClearing] = useState(false)
  const [activeTab, setActiveTab] = useState('upload')

  // useEffect runs when component mounts or when monthsToShow changes
  useEffect(() => {
    if (loggedIn) {
      fetchSpendingData()
    }
  }, [monthsToShow, loggedIn])

  // Function to fetch spending data from backend
  const fetchSpendingData = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await authFetch(`/reports/trends?months=${monthsToShow}`)

      if (!response.ok) {
        throw new Error('Failed to fetch spending data')
      }

      const data = await response.json()

      // Transform data for the chart - flatten nested objects into top-level keys
      const chartData = data.map(item => ({
        ...item,
        // Create label like "Mar 2026"
        label: new Date(item.year, item.month - 1).toLocaleDateString('en-GB', {
          month: 'short',
          year: 'numeric'
        }),
        // Flatten by_account and by_category into top-level keys
        ...Object.fromEntries(
          Object.entries(item.by_account || {}).map(([k, v]) => [`acct_${k}`, v])
        ),
        ...Object.fromEntries(
          Object.entries(item.by_category || {}).map(([k, v]) => [`cat_${k}`, v])
        ),
      }))

      setSpendingData(chartData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    clearToken()
    setLoggedIn(false)
  }

  if (!loggedIn) {
    return <Login onLogin={() => setLoggedIn(true)} />
  }

  // Calculate average spending (only months with data)
  const averageSpending = (() => {
    const totalSpending = spendingData.reduce((sum, item) => sum + item.total_spent, 0)
    const monthsWithData = spendingData.filter(item => item.total_spent > 0).length
    return monthsWithData > 0 ? totalSpending / monthsWithData : 0
  })()

  // Collect unique keys for stacked bars
  const accountKeys = [...new Set(spendingData.flatMap(d =>
    Object.keys(d).filter(k => k.startsWith('acct_'))
  ))]
  const categoryKeys = [...new Set(spendingData.flatMap(d =>
    Object.keys(d).filter(k => k.startsWith('cat_'))
  ))]

  const COLORS = ['#4f46e5', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1', '#14b8a6', '#e11d48', '#a855f7']

  // Custom tooltip component for hover information
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const total = payload.reduce((sum, p) => sum + (p.value || 0), 0)
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{label}</p>
          {stackMode === 'total' ? (
            <p className="tooltip-value">£{payload[0].value.toFixed(2)}</p>
          ) : (
            <>
              {payload.map((p, i) => (
                <p key={i} style={{ color: p.fill }}>
                  {p.name}: £{p.value.toFixed(2)}
                </p>
              ))}
              <p className="tooltip-value"><strong>Total: £{total.toFixed(2)}</strong></p>
            </>
          )}
          {averageSpending > 0 && (
            <p className="tooltip-average">Avg: £{averageSpending.toFixed(2)}</p>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <div className="app">
      <header>
        <h1>Monthly Spending</h1>
        <button className="logout-button" onClick={handleLogout}>Sign Out</button>
      </header>

      <div className="controls">
        <label htmlFor="months">Show last: </label>
        <select
          id="months"
          value={monthsToShow}
          onChange={(e) => setMonthsToShow(Number(e.target.value))}
        >
          <option value={3}>3 months</option>
          <option value={6}>6 months</option>
          <option value={12}>12 months</option>
        </select>

        <label htmlFor="stack-mode">Stack by: </label>
        <select
          id="stack-mode"
          value={stackMode}
          onChange={(e) => setStackMode(e.target.value)}
        >
          <option value="total">Total</option>
          <option value="account">Account</option>
          <option value="category">Category</option>
        </select>
      </div>

      <div className="chart-container">
        {loading && <p className="status">Loading...</p>}

        {error && (
          <p className="status error">
            Error: {error}. Make sure the backend is running.
          </p>
        )}

        {!loading && !error && spendingData.length > 0 && (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={spendingData}
              margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
              onClick={(e) => {
                if (e && e.activePayload && e.activePayload.length) {
                  const d = e.activePayload[0].payload
                  setSelectedMonth(d.month)
                  setSelectedYear(d.year)
                  setSelectionKey(k => k + 1)
                  setTimeout(() => {
                    reportRef.current?.scrollIntoView({ behavior: 'smooth' })
                  }, 100)
                }
              }}
              style={{ cursor: 'pointer' }}
            >
              {/* Grid lines for readability */}
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />

              {/* X-axis showing month labels */}
              <XAxis
                dataKey="label"
                angle={-45}
                textAnchor="end"
                height={80}
                tick={{ fontSize: 12 }}
              />

              {/* Y-axis showing spending in GBP */}
              <YAxis
                tickFormatter={(value) => `£${value}`}
                tick={{ fontSize: 12 }}
              />

              {/* Tooltip on hover */}
              <Tooltip content={<CustomTooltip />} />

              {/* Average spending line */}
              {averageSpending > 0 && (
                <ReferenceLine
                  y={averageSpending}
                  stroke="#ef4444"
                  strokeDasharray="5 5"
                  label={{ value: `Avg: £${averageSpending.toFixed(0)}`, position: 'right', fill: '#ef4444', fontSize: 12 }}
                />
              )}

              {/* Legend for stacked modes */}
              {stackMode !== 'total' && <Legend />}

              {/* The actual bars */}
              {stackMode === 'total' && (
                <Bar dataKey="total_spent" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              )}
              {stackMode === 'account' && accountKeys.map((key, i) => (
                <Bar
                  key={key}
                  dataKey={key}
                  name={key.replace('acct_', '')}
                  stackId="account"
                  fill={COLORS[i % COLORS.length]}
                />
              ))}
              {stackMode === 'category' && categoryKeys.map((key, i) => (
                <Bar
                  key={key}
                  dataKey={key}
                  name={key.replace('cat_', '')}
                  stackId="category"
                  fill={COLORS[i % COLORS.length]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        )}

        {!loading && !error && spendingData.length === 0 && (
          <p className="status">No spending data available</p>
        )}
      </div>

      <div ref={reportRef}>
        <MonthlyReport selectedMonth={selectedMonth} selectedYear={selectedYear} selectionKey={selectionKey} />
      </div>

      <div className="tab-bar">
        <button className={`tab ${activeTab === 'categorize' ? 'active' : ''}`} onClick={() => setActiveTab('categorize')}>Categorize</button>
        <button className={`tab ${activeTab === 'upload' ? 'active' : ''}`} onClick={() => setActiveTab('upload')}>Upload</button>
        <button className={`tab ${activeTab === 'exclusions' ? 'active' : ''}`} onClick={() => setActiveTab('exclusions')}>Exclusion Rules</button>
        <button className={`tab ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>Settings</button>
      </div>

      <div className="tab-content">
        {activeTab === 'categorize' && <Categorizer />}

        {activeTab === 'upload' && <UploadForm onUploadSuccess={fetchSpendingData} />}

        {activeTab === 'exclusions' && <ExclusionRules onRulesChanged={fetchSpendingData} />}

        {activeTab === 'settings' && (
          <div className="danger-zone">
            <h2>Danger Zone</h2>
            <p>This will permanently delete all transactions, categories, accounts, and rules.</p>
            <button
              className="danger-button"
              disabled={clearing}
              onClick={async () => {
                if (!window.confirm('Are you sure? This will delete ALL data.')) return
                setClearing(true)
                try {
                  const res = await authFetch('/admin/clear-database', { method: 'POST' })
                  if (!res.ok) throw new Error('Failed to clear')
                  const data = await res.json()
                  alert(`Database cleared. Deleted: ${data.deleted.transactions} transactions, ${data.deleted.categories} categories, ${data.deleted.accounts} accounts.`)
                  fetchSpendingData()
                } catch (err) {
                  alert('Error clearing database: ' + err.message)
                } finally {
                  setClearing(false)
                }
              }}
            >
              {clearing ? 'Clearing...' : 'Clear Database'}
            </button>
          </div>
        )}
      </div>

      <footer>
        <p>Data from your budgeting app API</p>
      </footer>
    </div>
  )
}

export default App
