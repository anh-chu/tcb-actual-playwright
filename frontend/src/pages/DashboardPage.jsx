import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const RANGE_KEY = 'tcb-sync-date-range'

const isoDay = (d) => d.toISOString().split('T')[0]

const daysAgo = (n) => {
    const d = new Date()
    d.setDate(d.getDate() - n)
    return isoDay(d)
}

const monthStart = () => {
    const d = new Date()
    return isoDay(new Date(d.getFullYear(), d.getMonth(), 1))
}

const PRESETS = [
    { label: '7d', from: () => daysAgo(7), to: () => isoDay(new Date()) },
    { label: '30d', from: () => daysAgo(30), to: () => isoDay(new Date()) },
    { label: '90d', from: () => daysAgo(90), to: () => isoDay(new Date()) },
    { label: 'This month', from: monthStart, to: () => isoDay(new Date()) },
]

function DashboardPage() {
    const [status, setStatus] = useState('idle')
    const [lastError, setLastError] = useState('')
    const [logs, setLogs] = useState([])
    const [lastResult, setLastResult] = useState(null)
    const [banner, setBanner] = useState(null)
    const { logout, user } = useAuth()
    const navigate = useNavigate()
    const logBoxRef = useRef(null)

    const getInitialRange = () => {
        try {
            const saved = JSON.parse(localStorage.getItem(RANGE_KEY) || 'null')
            if (saved?.from && saved?.to) return saved
        } catch { /* fall through to default */ }
        return { from: daysAgo(30), to: isoDay(new Date()) }
    }

    const [dateRange, setDateRange] = useState(getInitialRange)

    // Remember the range: re-picking it on every visit was pure friction.
    useEffect(() => {
        try {
            localStorage.setItem(RANGE_KEY, JSON.stringify(dateRange))
        } catch { /* ignore quota/private mode */ }
    }, [dateRange])

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await axios.get('/api/status')
                setStatus(res.data.status)
                setLogs(res.data.logs || [])
                setLastError(res.data.last_error)
                setLastResult(res.data.last_result || null)
            } catch (e) {
                console.error(e)
            }
        }
        const interval = setInterval(fetchStatus, 1000)
        fetchStatus()
        return () => clearInterval(interval)
    }, [])

    // Keep the newest log line in view as the sync runs.
    useEffect(() => {
        const box = logBoxRef.current
        if (box) box.scrollTop = box.scrollHeight
    }, [logs])

    const handleStart = async () => {
        if (dateRange.from > dateRange.to) {
            setBanner({ kind: 'error', msg: 'The "from" date is after the "to" date.' })
            return
        }
        setBanner(null)
        try {
            await axios.post('/api/sync/start', {
                date_from: dateRange.from,
                date_to: dateRange.to
            })
        } catch (e) {
            const detail = e.response?.data?.detail || e.message
            if (e.response?.status === 409) {
                setBanner({ kind: 'warning', msg: 'A sync is already running.' })
            } else if (detail.includes('Settings not configured')) {
                setBanner({ kind: 'warning', msg: 'No credentials saved yet.', action: 'settings' })
            } else {
                setBanner({ kind: 'error', msg: 'Failed to start: ' + detail })
            }
        }
    }

    const handleStop = async () => {
        try {
            await axios.post('/api/sync/stop')
        } catch (e) {
            setBanner({ kind: 'error', msg: 'Failed to stop: ' + e.message })
        }
    }

    const applyPreset = (preset) => {
        setDateRange({ from: preset.from(), to: preset.to() })
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

    const shortId = (id) => (id && id.length > 12 ? `${id.slice(0, 8)}…` : id)

    const isRunning = status !== 'idle' && status !== 'error' && status !== 'success'
    const isWaitingOtp = status === 'waiting_otp'
    const isPresetActive = (preset) =>
        dateRange.from === preset.from() && dateRange.to === preset.to()

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
                            Action required — verify the login on the Techcombank mobile app
                        </div>
                    )}

                    {banner && (
                        <div className={`alert alert-${banner.kind}`} style={{ marginBottom: '1.25rem' }}>
                            {banner.msg}{' '}
                            {banner.action === 'settings' && (
                                <span
                                    style={{ cursor: 'pointer', textDecoration: 'underline' }}
                                    onClick={() => navigate('/settings')}
                                >
                                    Open Settings
                                </span>
                            )}
                        </div>
                    )}

                    {/* Controls */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                            {PRESETS.map((p) => (
                                <button
                                    key={p.label}
                                    type="button"
                                    className={`btn-ghost btn-sm${isPresetActive(p) ? ' btn-active' : ''}`}
                                    onClick={() => applyPreset(p)}
                                    disabled={isRunning}
                                >
                                    {p.label}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flexWrap: 'wrap', marginTop: '0.875rem' }}>
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

                    {/* Last run summary */}
                    {!isRunning && lastResult && (
                        <>
                            <div className="divider" />
                            <p className="field-label" style={{ marginBottom: '0.625rem' }}>Last Run</p>
                            <div className="summary-grid">
                                <div className="summary-stat">
                                    <span className="summary-value">{lastResult.transactions_fetched ?? 0}</span>
                                    <span className="summary-label">fetched</span>
                                </div>
                                <div className="summary-stat">
                                    <span className="summary-value">{lastResult.total_added ?? 0}</span>
                                    <span className="summary-label">added</span>
                                </div>
                                <div className="summary-stat">
                                    <span className="summary-value">{lastResult.total_updated ?? 0}</span>
                                    <span className="summary-label">updated</span>
                                </div>
                                <div className="summary-stat">
                                    <span
                                        className="summary-value"
                                        style={{ color: lastResult.skipped_unmapped ? 'var(--warning)' : undefined }}
                                    >
                                        {lastResult.skipped_unmapped ?? 0}
                                    </span>
                                    <span className="summary-label">skipped</span>
                                </div>
                            </div>
                            <p className="field-hint">
                                {lastResult.date_from} → {lastResult.date_to}
                                {lastResult.finished_at ? ` · finished ${lastResult.finished_at.replace('T', ' ')}` : ''}
                            </p>
                            {lastResult.skipped_unmapped > 0 && (
                                <div className="alert alert-warning" style={{ marginTop: '0.75rem' }}>
                                    {lastResult.skipped_unmapped} transaction(s) skipped because their
                                    arrangement is not mapped:{' '}
                                    {Object.entries(lastResult.unmapped_arrangements || {}).map(
                                        ([id, n]) => `${n}× ${id}`
                                    ).join(', ')}{' '}
                                    <span
                                        style={{ cursor: 'pointer', textDecoration: 'underline' }}
                                        onClick={() => navigate('/settings')}
                                    >
                                        Add mapping
                                    </span>
                                </div>
                            )}
                            {Object.keys(lastResult.accounts || {}).length > 0 && (
                                <div className="summary-accounts">
                                    {Object.entries(lastResult.accounts).map(([id, s]) => (
                                        <div key={id} className="summary-account">
                                            <span className="input-mono" title={id}>{shortId(id)}</span>
                                            <span style={{ color: 'var(--text-muted)' }}>
                                                {s.sent} sent · {s.added} added · {s.updated} updated
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}

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
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.625rem' }}>
                                    <p className="field-label" style={{ margin: 0 }}>Activity</p>
                                    <button
                                        type="button"
                                        className="btn-ghost btn-sm"
                                        onClick={() => {
                                            const text = logs.join('\n')
                                            if (navigator.clipboard) navigator.clipboard.writeText(text)
                                        }}
                                    >
                                        Copy
                                    </button>
                                </div>
                                <div className="log-container" ref={logBoxRef}>
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
