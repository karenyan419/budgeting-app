import { useState, useEffect } from 'react'
import { authFetch } from '../auth'

function ExclusionRules({ onRulesChanged }) {
  const [rules, setRules] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [newRule, setNewRule] = useState({ description_pattern: '', bank: '', amount: '', notes: '' })
  const [adding, setAdding] = useState(false)
  const [applying, setApplying] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [message, setMessage] = useState(null)
  const [excludedTxs, setExcludedTxs] = useState([])
  const [showExcluded, setShowExcluded] = useState(false)
  const [loadingTxs, setLoadingTxs] = useState(false)

  const fetchRules = () => {
    setLoading(true)
    authFetch('/exclusions/')
      .then(res => res.json())
      .then(data => { setRules(data); setError(null) })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }

  const fetchExcludedTxs = () => {
    setLoadingTxs(true)
    authFetch('/transactions/?excluded=true')
      .then(res => res.json())
      .then(data => setExcludedTxs(data))
      .catch(() => {})
      .finally(() => setLoadingTxs(false))
  }

  useEffect(() => { fetchRules() }, [])

  useEffect(() => {
    if (showExcluded) fetchExcludedTxs()
  }, [showExcluded])

  const handleAdd = async (e) => {
    e.preventDefault()
    if (!newRule.description_pattern.trim()) return

    setAdding(true)
    try {
      const body = {
        description_pattern: newRule.description_pattern.trim(),
        notes: newRule.notes.trim() || null,
        bank: newRule.bank || null,
        amount: newRule.amount ? Number(newRule.amount) : null,
      }
      const res = await authFetch('/exclusions/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error('Failed to add rule')
      setNewRule({ description_pattern: '', bank: '', amount: '', notes: '' })
      fetchRules()
    } catch (err) {
      setError(err.message)
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this exclusion rule?')) return
    try {
      const res = await authFetch(`/exclusions/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete')
      fetchRules()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleApplyAll = async () => {
    setApplying(true)
    setMessage(null)
    try {
      const res = await authFetch('/exclusions/apply-all', { method: 'POST' })
      if (!res.ok) throw new Error('Failed to apply')
      const data = await res.json()
      setMessage(`Applied to ${data.total} transactions. ${data.excluded} excluded.`)
      if (showExcluded) fetchExcludedTxs()
      if (onRulesChanged) onRulesChanged()
    } catch (err) {
      setError(err.message)
    } finally {
      setApplying(false)
    }
  }

  const handleReset = async () => {
    if (!window.confirm('This will un-exclude ALL transactions. Are you sure?')) return
    setResetting(true)
    setMessage(null)
    try {
      const res = await authFetch('/exclusions/reset', { method: 'POST' })
      if (!res.ok) throw new Error('Failed to reset')
      const data = await res.json()
      setMessage(`Reset ${data.reset} transactions to not excluded.`)
      if (showExcluded) fetchExcludedTxs()
      if (onRulesChanged) onRulesChanged()
    } catch (err) {
      setError(err.message)
    } finally {
      setResetting(false)
    }
  }

  return (
    <div className="exclusion-rules">
      <h2>Exclusion Rules</h2>
      <p className="exclusion-desc">
        Transactions matching these patterns are excluded from spending reports.
      </p>

      {loading && <p className="status">Loading...</p>}
      {error && <p className="status error">Error: {error}</p>}
      {message && <p className="exclusion-message">{message}</p>}

      {!loading && (
        <>
          <table className="exclusion-table">
            <thead>
              <tr>
                <th>Pattern</th>
                <th>Bank</th>
                <th>Amount</th>
                <th>Notes</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rules.map(rule => (
                <tr key={rule.id}>
                  <td className="pattern-cell">{rule.description_pattern}</td>
                  <td>{rule.bank || 'Any'}</td>
                  <td>{rule.amount != null ? `£${rule.amount.toFixed(2)}` : 'Any'}</td>
                  <td className="notes-cell">{rule.notes || ''}</td>
                  <td>
                    <button className="delete-rule-button" onClick={() => handleDelete(rule.id)}>
                      &times;
                    </button>
                  </td>
                </tr>
              ))}
              {rules.length === 0 && (
                <tr><td colSpan={5} className="status">No exclusion rules</td></tr>
              )}
            </tbody>
          </table>

          <form className="add-rule-form" onSubmit={handleAdd}>
            <input
              type="text"
              placeholder="Description pattern"
              value={newRule.description_pattern}
              onChange={(e) => setNewRule({ ...newRule, description_pattern: e.target.value })}
              required
            />
            <select
              value={newRule.bank}
              onChange={(e) => setNewRule({ ...newRule, bank: e.target.value })}
            >
              <option value="">Any bank</option>
              <option value="monzo">Monzo</option>
              <option value="yonder">Yonder</option>
            </select>
            <input
              type="number"
              step="0.01"
              placeholder="Amount (optional)"
              value={newRule.amount}
              onChange={(e) => setNewRule({ ...newRule, amount: e.target.value })}
            />
            <input
              type="text"
              placeholder="Notes (optional)"
              value={newRule.notes}
              onChange={(e) => setNewRule({ ...newRule, notes: e.target.value })}
            />
            <button type="submit" disabled={adding}>
              {adding ? 'Adding...' : 'Add Rule'}
            </button>
          </form>

          <div className="exclusion-actions">
            <button
              className="apply-rules-button"
              disabled={applying}
              onClick={handleApplyAll}
            >
              {applying ? 'Applying...' : 'Apply Rules to All Transactions'}
            </button>
            <button
              className="reset-rules-button"
              disabled={resetting}
              onClick={handleReset}
            >
              {resetting ? 'Resetting...' : 'Reset All Exclusions'}
            </button>
          </div>

          <button
            className="toggle-transactions"
            onClick={() => setShowExcluded(!showExcluded)}
          >
            {showExcluded ? 'Hide' : 'Show'} Excluded Transactions
          </button>

          {showExcluded && (
            <div className="transactions-table-wrapper">
              {loadingTxs && <p className="status">Loading...</p>}
              {!loadingTxs && excludedTxs.length === 0 && (
                <p className="status">No excluded transactions</p>
              )}
              {!loadingTxs && excludedTxs.length > 0 && (
                <table className="transactions-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Description</th>
                      <th>Amount</th>
                      <th>Account</th>
                    </tr>
                  </thead>
                  <tbody>
                    {excludedTxs.map(tx => (
                      <tr key={tx.id}>
                        <td>{tx.date}</td>
                        <td className="tx-description">{tx.description}</td>
                        <td className={tx.amount < 0 ? 'amount-negative' : 'amount-positive'}>
                          {tx.amount < 0 ? '-' : '+'}£{Math.abs(tx.amount).toFixed(2)}
                        </td>
                        <td>{tx.account_name || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default ExclusionRules
