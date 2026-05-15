import { useState, useEffect, useCallback } from 'react'
import { authFetch } from '../auth'

// Build shortcut keys: 1-9, then a-z (excluding s and u which are reserved)
const SHORTCUT_KEYS = ['1','2','3','4','5','6','7','8','9','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','t','v','w','x','y','z']

function Categorizer() {
  const [transactions, setTransactions] = useState([])
  const [categories, setCategories] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [score, setScore] = useState(0)
  const [streak, setStreak] = useState(0)
  const [animation, setAnimation] = useState(null)
  const [history, setHistory] = useState([])

  const fetchData = useCallback(() => {
    setLoading(true)
    Promise.all([
      authFetch('/transactions/?excluded=false').then(r => r.json()),
      authFetch('/categories/').then(r => r.json()),
    ]).then(([txData, catData]) => {
      const generalCat = catData.find(c => c.name.toLowerCase() === 'general')
      const generalId = generalCat ? generalCat.id : null

      const uncategorized = txData.filter(tx =>
        tx.amount < 0 && (tx.category_id === null || tx.category_id === generalId)
      )

      // Shuffle
      for (let i = uncategorized.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [uncategorized[i], uncategorized[j]] = [uncategorized[j], uncategorized[i]]
      }

      setTransactions(uncategorized)
      setCategories(catData.filter(c => c.name.toLowerCase() !== 'general'))
      setCurrentIndex(0)
      setScore(0)
      setStreak(0)
      setHistory([])
    }).finally(() => setLoading(false))
  }, [])

  useEffect(() => { fetchData() }, [fetchData])

  const current = transactions[currentIndex]
  const remaining = transactions.length - currentIndex
  const total = transactions.length

  const categoryKeyMap = {}
  categories.forEach((cat, i) => {
    if (i < SHORTCUT_KEYS.length) {
      categoryKeyMap[SHORTCUT_KEYS[i]] = cat
    }
  })

  const handleCategorize = useCallback(async (categoryId) => {
    if (saving || !current) return
    setSaving(true)
    setAnimation('swoosh')

    try {
      const res = await authFetch(`/transactions/${current.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category_id: categoryId }),
      })
      if (!res.ok) throw new Error('Failed to save')

      setHistory(h => [...h, { txId: current.id, prevCategoryId: current.category_id }])
      setScore(s => s + 1)
      setStreak(s => s + 1)

      setTimeout(() => {
        setAnimation(null)
        setCurrentIndex(i => i + 1)
        setSaving(false)
      }, 250)
    } catch {
      setSaving(false)
      setAnimation(null)
    }
  }, [saving, current])

  const handleSkip = useCallback(() => {
    if (saving || !current) return
    setStreak(0)
    setAnimation('skip')
    setTimeout(() => {
      setAnimation(null)
      setCurrentIndex(i => i + 1)
    }, 150)
  }, [saving, current])

  const handleUndo = useCallback(async () => {
    if (saving || history.length === 0) return
    const last = history[history.length - 1]
    setSaving(true)

    try {
      const res = await authFetch(`/transactions/${last.txId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category_id: last.prevCategoryId }),
      })
      if (res.ok) {
        setHistory(h => h.slice(0, -1))
        setCurrentIndex(i => Math.max(0, i - 1))
        setScore(s => Math.max(0, s - 1))
        setStreak(0)
      }
    } finally {
      setSaving(false)
    }
  }, [saving, history])

  // Keyboard handler
  useEffect(() => {
    const handler = (e) => {
      // Don't capture when typing in inputs
      const tag = document.activeElement?.tagName?.toLowerCase()
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return

      const key = e.key.toLowerCase()

      if (key === 's') {
        e.preventDefault()
        handleSkip()
        return
      }
      if (key === 'u') {
        e.preventDefault()
        handleUndo()
        return
      }

      const matched = categoryKeyMap[key]
      if (matched) {
        e.preventDefault()
        handleCategorize(matched.id)
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [categoryKeyMap, handleCategorize, handleSkip, handleUndo])

  if (loading) {
    return <div className="categorizer"><p className="status">Loading transactions...</p></div>
  }

  if (total === 0) {
    return (
      <div className="categorizer">
        <div className="cat-done">
          <h2>All done!</h2>
          <p>No uncategorized transactions to sort.</p>
          <button className="cat-refresh" onClick={fetchData}>Refresh</button>
        </div>
      </div>
    )
  }

  if (!current) {
    return (
      <div className="categorizer">
        <div className="cat-done">
          <h2>Session complete!</h2>
          <p>You categorized <strong>{score}</strong> transaction{score !== 1 ? 's' : ''}.</p>
          <button className="cat-refresh" onClick={fetchData}>Play Again</button>
        </div>
      </div>
    )
  }

  return (
    <div className="categorizer">
      <div className="cat-header">
        <h2>Categorize Transactions</h2>
        <div className="cat-stats">
          <span className="cat-score">{score} done</span>
          {streak >= 3 && <span className="cat-streak">{streak} streak!</span>}
          <span className="cat-remaining">{remaining} left</span>
        </div>
      </div>

      <div className="cat-progress">
        <div className="cat-progress-fill" style={{ width: `${total > 0 ? ((total - remaining) / total) * 100 : 0}%` }} />
      </div>

      <div className={`cat-card ${animation || ''}`}>
        <p className="cat-date">{current.date}</p>
        <p className="cat-description">{current.description}</p>
        <div className="cat-card-footer">
          <span className="cat-amount">£{Math.abs(current.amount).toFixed(2)}</span>
          {current.account_name && <span className="cat-account">{current.account_name}</span>}
        </div>
      </div>

      <div className="cat-buttons">
        {categories.map((cat, i) => {
          const key = i < SHORTCUT_KEYS.length ? SHORTCUT_KEYS[i] : null
          return (
            <button
              key={cat.id}
              className="cat-choice"
              disabled={saving}
              onClick={() => handleCategorize(cat.id)}
            >
              {key && <span className="cat-key">{key.toUpperCase()}</span>}
              {cat.name}
            </button>
          )
        })}
      </div>

      <div className="cat-actions">
        <button className="cat-skip" onClick={handleSkip} disabled={saving}>
          <span className="cat-key">S</span> Skip
        </button>
        <button className="cat-undo" onClick={handleUndo} disabled={saving || history.length === 0}>
          <span className="cat-key">U</span> Undo
        </button>
      </div>
    </div>
  )
}

export default Categorizer
