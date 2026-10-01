import { useState, useEffect } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

function DashboardPage() {
    const [status, setStatus] = useState('idle')
    const [lastError, setLastError] = useState('')
    const [logs, setLogs] = useState([])
    const { logout, user } = useAuth()
    const navigate = useNavigate()

    const getDefaultDates = () => {
        const today = new Date()
        const monthAgo = new Date()
        monthAgo.setDate(monthAgo.getDate() - 30)
        return {
            from: monthAgo.toISOString().split('T')[0],
            to: today.toISOString().split('T')[0]
        }
    }

    const [dateRange, setDateRange] = useState(getDefaultDates())

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await axios.get('/api/status')
                setStatus(res.data.status)
                setLogs(res.data.logs || [])
                setLastError(res.data.last_error)
            } catch (e) {
                console.error(e)
            }
        }
        const interval = setInterval(fetchStatus, 1000)
        fetchStatus()
        return () => clearInterval(interval)
    }, [])

    const handleStart = async () => {
        try {
            await axios.post('/api/sync/start', {
                date_from: dateRange.from,
                date_to: dateRange.to
            })
        } catch (e) {
            if (e.response?.status === 400 && e.response.data.detail.includes('Settings not configured')) {
                alert('Please configure settings first!')
                navigate('/settings')
            } else {
                alert('Failed to start: ' + (e.response?.data?.detail || e.message))
            }
        }
    }

    const handleStop = async () => {
        try {
            await axios.post('/api/sync/stop')
        } catch (e) {
            alert('Failed to stop: ' + e.message)
        }
    }

    const getStatusClass = () => {
        if (status === 'idle' || status === 'error' || status === 'success') return `status-${status}`
        if (status === 'waiting_otp') return 'status-waiting_otp'
        return 'status-running'
    }

    const formatLogEntry = (log) => {
        let type = 'info'
        if (log.toLowerCase().includes('[error]') || log.toLowerCase().includes('failed')) type = 'error'
        if (log.toLowerCase().includes('[success]') || log.toLowerCase().includes('done')) type = 'success'
        if (log.toLowerCase().includes('[warning]') || log.toLowerCase().includes('timeout')) type = 'warning'
        return { content: log, className: `log-entry log-${type}` }
    }

    const isRunning = status !== 'idle' && status !== 'error' && status !== 'success'
    const isWaitingOtp = status === 'waiting_otp'

    return (
        <div className="app-shell">
            <nav className="top-nav">
                <span className="top-nav-brand">TCB → Actual</span>
                <div className="top-nav-actions">
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{user?.username}</span>
                    <button className="btn-ghost btn-sm" onClick={() => navigate('/settings')}>Settings</button>
                    <button className="btn-danger btn-sm" onClick={logout}>Logout</button>
                </div>
            </nav>

            <main className="page-content">
                <div className="page-header">
                    <h1>Sync</h1>
                    <p>Push Techcombank transactions to Actual Budget</p>
                </div>

                <div className="card">
                    {/* Status row */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
                        <span className={`status-badge ${getStatusClass()}`}>
                            {status.replace('_', ' ')}
                        </span>
                        {lastError && (
                            <span style={{ fontSize: '0.75rem', color: 'var(--error)' }}>{lastError}</span>
                        )}
                    </div>

                    {isWaitingOtp && (
                        <div className="alert alert-warning" style={{ marginBottom: '1.25rem' }}>
                            Action required — verify OTP on your mobile app
                        </div>
                    )}

                    {/* Controls */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flexWrap: 'wrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span className="field-label" style={{ whiteSpace: 'nowrap' }}>From</span>
                            <input
                                type="date"
                                className="input-modern"
                                style={{ width: 'auto' }}
                                value={dateRange.from}
                                onChange={(e) => setDateRange({ ...dateRange, from: e.target.value })}
                                disabled={isRunning}
                            />
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span className="field-label" style={{ whiteSpace: 'nowrap' }}>To</span>
                            <input
                                type="date"
                                className="input-modern"
                                style={{ width: 'auto' }}
                                value={dateRange.to}
                                onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })}
                                disabled={isRunning}
                            />
                        </div>
                        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
                            <button onClick={handleStart} disabled={isRunning}>
                                {isRunning ? 'Syncing...' : 'Start Sync'}
                            </button>
                            {isRunning && (
                                <button className="btn-danger" onClick={handleStop}>Stop</button>
                            )}
                        </div>
                    </div>

                    {/* Stream + Logs */}
                    {(isRunning || logs.length > 0) && (
                        <>
                            <div className="divider" />

                            {isRunning && (
                                <div style={{ marginBottom: '1.25rem' }}>
                                    <p className="field-label" style={{ marginBottom: '0.625rem' }}>Live Browser</p>
                                    <div style={{ borderRadius: '6px', overflow: 'hidden', background: '#000', aspectRatio: '16/9' }}>
                                        <img
                                            src="/api/stream"
                                            style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
                                            alt="Browser Stream"
                                        />
                                    </div>
                                </div>
                            )}

                            <div>
                                <p className="field-label" style={{ marginBottom: '0.625rem' }}>Activity</p>
                                <div className="log-container">
                                    {logs.length === 0 && (
                                        <span style={{ color: 'var(--text-muted)' }}>Waiting...</span>
                                    )}
                                    {logs.map((log, i) => {
                                        const entry = formatLogEntry(log)
                                        return <div key={i} className={entry.className}>{entry.content}</div>
                                    })}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </main>
        </div>
    )
}

export default DashboardPage
