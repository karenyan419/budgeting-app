import { useState, useEffect } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer
} from 'recharts'
import './App.css'

// Backend API URL - change this if your backend is on a different port
const API_URL = 'http://localhost:8000'

function App() {
  // State for storing spending data from API
  const [spendingData, setSpendingData] = useState([])
  // State for how many months to show (default: 6)
  const [monthsToShow, setMonthsToShow] = useState(6)
  // State for loading indicator
  const [loading, setLoading] = useState(true)
  // State for error messages
  const [error, setError] = useState(null)

  // useEffect runs when component mounts or when monthsToShow changes
  useEffect(() => {
    fetchSpendingData()
  }, [monthsToShow])

  // Function to fetch spending data from backend
  const fetchSpendingData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Call the /reports/trends endpoint with months parameter
      const response = await fetch(`${API_URL}/reports/trends?months=${monthsToShow}`)

      if (!response.ok) {
        throw new Error('Failed to fetch spending data')
      }

      const data = await response.json()

      // Transform data for the chart - add readable month labels
      const chartData = data.map(item => ({
        ...item,
        // Create label like "Mar 2026"
        label: new Date(item.year, item.month - 1).toLocaleDateString('en-GB', {
          month: 'short',
          year: 'numeric'
        })
      }))

      setSpendingData(chartData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Calculate average spending (only months with data)
  const averageSpending = (() => {
    const totalSpending = spendingData.reduce((sum, item) => sum + item.total_spent, 0)
    const monthsWithData = spendingData.filter(item => item.total_spent > 0).length
    return monthsWithData > 0 ? totalSpending / monthsWithData : 0
  })()

  // Custom tooltip component for hover information
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="tooltip-label">{label}</p>
          <p className="tooltip-value">£{payload[0].value.toFixed(2)}</p>
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
            <BarChart data={spendingData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
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

              {/* The actual bars */}
              <Bar
                dataKey="total_spent"
                fill="#4f46e5"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        )}

        {!loading && !error && spendingData.length === 0 && (
          <p className="status">No spending data available</p>
        )}
      </div>

      <footer>
        <p>Data from your budgeting app API</p>
      </footer>
    </div>
  )
}

export default App
