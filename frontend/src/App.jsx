import { useState, useEffect } from 'react'

function App() {
  const [status, setStatus] = useState('idle')
  const [logs, setLogs] = useState([])
  const [lastError, setLastError] = useState('')
  const [loading, setLoading] = useState(false)

  // Determine API base URL
  // In development, Vite proxys or we just point to localhost:8000
  // In production, it's relative
  const API_BASE = import.meta.env.DEV ? 'http://localhost:8000' : ''

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`)
      const data = await res.json()
      setStatus(data.status)
      setLogs(data.logs || [])
      setLastError(data.last_error)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    const interval = setInterval(fetchStatus, 1000)
    return () => clearInterval(interval)
  }, [])

  const handleStart = async () => {
    setLoading(true)
    try {
      await fetch(`${API_BASE}/api/sync/start`, { method: 'POST' })
    } catch (e) {
      alert("Failed to start sync")
    }
    setLoading(false)
  }

  const handleStop = async () => {
    try {
      await fetch(`${API_BASE}/api/sync/stop`, { method: 'POST' })
    } catch (e) {
      console.error(e)
    }
  }

  const getStatusLabel = (s) => {
    return s.replace('_', ' ').toUpperCase()
  }

  const isRunning = status !== 'idle' && status !== 'error' && status !== 'success'
  const isWaitingOtp = status === 'waiting_otp'

  return (
    <div className="container">
      <div className="card">
        <h1>Techcombank Sync</h1>
        <p style={{ color: '#94a3b8' }}>Automated transaction import for Actual Budget</p>

        <div style={{ textAlign: 'center', margin: '2rem 0' }}>
          <div className={`status-badge status-${status}`}>
            {getStatusLabel(status)}
          </div>
        </div>

        {lastError && (
          <pre>{lastError}</pre>
        )}

        {!isRunning ? (
          <button className="btn" onClick={handleStart} disabled={loading}>
            {loading ? 'Starting...' : 'Start Sync Now'}
          </button>
        ) : (
          <button className="btn btn-stop" onClick={handleStop}>
            Stop Sync
          </button>
        )}
      </div>

      {/* Show VNC when running, or at least when it might be useful. 
          Actually, let's always show it if running, so user can see progress. */}
      {/* Show VNC when running, or at least when it might be useful. 
          Actually, let's always show it if running, so user can see progress. */}
      {isRunning && (
        <>
          <div className="card" style={{ maxWidth: '1000px' }}>
            <h2 style={{ margin: '0 0 1rem 0' }}>Live View</h2>
            {isWaitingOtp && (
              <div style={{ background: '#f59e0b', color: 'black', padding: '0.5rem', borderRadius: '4px', marginBottom: '1rem', fontWeight: 'bold' }}>
                ⚠️ Action Required: Please enter OTP/Credentials in the view below.
              </div>
            )}
            <div className="vnc-container" style={{ display: 'flex', justifyContent: 'center', background: 'black' }}>
              <img src={`${API_BASE}/api/stream`} style={{ maxHeight: '100%', maxWidth: '100%', objectFit: 'contain' }} />
            </div>
          </div>

          <div className="card" style={{ maxWidth: '1000px', marginTop: '1rem' }}>
            <h2 style={{ margin: '0 0 1rem 0' }}>Logs</h2>
            <div style={{ background: 'rgba(0,0,0,0.5)', padding: '1rem', borderRadius: '8px', maxHeight: '300px', overflowY: 'auto', textAlign: 'left', fontFamily: 'monospace', fontSize: '0.9rem' }}>
              {logs.length === 0 && <span style={{ color: '#64748b' }}>No logs yet...</span>}
              {logs.map((log, i) => (
                <div key={i} style={{ marginBottom: '0.25rem' }}>{log}</div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default App
