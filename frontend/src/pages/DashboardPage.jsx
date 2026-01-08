import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import reactLogo from '../assets/react.svg'
import viteLogo from '/vite.svg'
import '../App.css'

function DashboardPage() {
    const [status, setStatus] = useState('idle')
    const [lastError, setLastError] = useState('')
    const [logs, setLogs] = useState([])
    const { logout, user } = useAuth()
    const navigate = useNavigate()

    // Date range state (default to last 30 days)
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

    // Polling for status
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
            if (e.response && e.response.status === 400 && e.response.data.detail.includes("Settings not configured")) {
                alert("Please configure settings first!");
                navigate('/settings');
            } else {
                alert("Failed to start: " + (e.response?.data?.detail || e.message))
            }
        }
    }

    const handleStop = async () => {
        try {
            await axios.post('/api/sync/stop')
        } catch (e) {
            alert("Failed to stop: " + e.message)
        }
    }

    const getStatusClass = () => {
        if (status === 'idle' || status === 'error' || status === 'success') {
            return `status-${status}`
        }
        if (status === 'waiting_otp') return 'status-waiting_otp'
        return 'status-running'
    }

    const formatLogEntry = (log) => {
        let type = 'info'
        if (log.toLowerCase().includes('[error]') || log.toLowerCase().includes('failed')) type = 'error'
        if (log.toLowerCase().includes('[success]') || log.toLowerCase().includes('done')) type = 'success'
        if (log.toLowerCase().includes('[warning]') || log.toLowerCase().includes('timeout')) type = 'warning'

        return {
            content: log,
            className: `log-entry log-${type}`
        }
    }

    const isRunning = status !== 'idle' && status !== 'error' && status !== 'success'
    const isWaitingOtp = status === 'waiting_otp'

    return (
        <div className="container">
            <div className="nav-bar">
                <span className="nav-user">Welcome, <strong>{user?.username}</strong></span>
                <button className="btn-secondary" style={{ padding: '0.5rem 1rem' }} onClick={() => navigate('/settings')}>Settings</button>
                <button className="btn-danger" style={{ padding: '0.5rem 1rem' }} onClick={logout}>Logout</button>
            </div>

            <h1 style={{ marginBottom: '3rem' }}>Actual TCB Sync</h1>

            <div className="glass-card" style={{ maxWidth: '800px', margin: '0 auto' }}>
                <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
                    <div style={{ marginBottom: '1rem' }}>
                        <span className={`status-badge ${getStatusClass()}`}>
                            {status.replace('_', ' ')}
                        </span>
                    </div>
                    {lastError && (
                        <div style={{ color: 'var(--error)', background: 'rgba(244, 63, 94, 0.1)', padding: '0.75rem', borderRadius: '12px', fontSize: '0.9rem', marginBottom: '1.5rem', border: '1px solid rgba(244, 63, 94, 0.2)' }}>
                            <strong>Error:</strong> {lastError}
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center', justifyContent: 'center', marginBottom: '2rem', flexWrap: 'wrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>FROM</span>
                            <input
                                type="date"
                                className="input-modern"
                                style={{ width: 'auto' }}
                                value={dateRange.from}
                                onChange={(e) => setDateRange({ ...dateRange, from: e.target.value })}
                                disabled={isRunning}
                            />
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>TO</span>
                            <input
                                type="date"
                                className="input-modern"
                                style={{ width: 'auto' }}
                                value={dateRange.to}
                                onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })}
                                disabled={isRunning}
                            />
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                        <button onClick={handleStart} disabled={isRunning} style={{ minWidth: '180px' }}>
                            {isRunning ? 'Syncing...' : 'Start Global Sync'}
                        </button>
                        {isRunning && (
                            <button className="btn-danger" onClick={handleStop} style={{ minWidth: '140px' }}>
                                Force Stop
                            </button>
                        )}
                    </div>
                </div>

                {(isRunning || logs.length > 0) && (
                    <div style={{ borderTop: '1px solid var(--glass-border)', paddingTop: '2rem' }}>
                        {isRunning && (
                            <div style={{ marginBottom: '2rem' }}>
                                <h3 style={{ fontSize: '1.2rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>Live Browser Session</h3>
                                {isWaitingOtp && (
                                    <div style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--warning)', padding: '1rem', marginBottom: '1rem', borderRadius: '12px', border: '1px solid rgba(245, 158, 11, 0.2)', fontSize: '0.9rem', fontWeight: '500' }}>
                                        ⚠️ Action Required: Verify OTP on your mobile app
                                    </div>
                                )}
                                <div style={{ border: '2px solid var(--glass-border)', borderRadius: '16px', overflow: 'hidden', height: '400px', width: '100%', background: '#000', margin: '0 auto', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }}>
                                    <img
                                        src="/api/stream"
                                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                                        alt="Browser Stream"
                                    />
                                </div>
                            </div>
                        )}

                        <div style={{ textAlign: 'left' }}>
                            <h3 style={{ fontSize: '1.2rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>Activity Logs</h3>
                            <div className="log-container">
                                {logs.length === 0 && <div style={{ color: 'var(--text-muted)', opacity: '0.5' }}>Waiting for activity...</div>}
                                {logs.map((log, i) => {
                                    const entry = formatLogEntry(log)
                                    return <div key={i} className={entry.className}>{entry.content}</div>
                                })}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default DashboardPage
