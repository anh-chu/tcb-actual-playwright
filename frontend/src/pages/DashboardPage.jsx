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

    const isRunning = status !== 'idle' && status !== 'error' && status !== 'success'
    const isWaitingOtp = status === 'waiting_otp'

    return (
        <>
            <div style={{ position: 'absolute', top: '1rem', right: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <span>Hello, {user?.username}</span>
                <button onClick={() => navigate('/settings')} style={{ padding: '0.4rem' }}>Settings</button>
                <button onClick={logout} style={{ background: '#b91c1c', padding: '0.4rem' }}>Logout</button>
            </div>

            <h1>Techcombank Sync</h1>
            <div className="card">
                <div style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #444', borderRadius: '8px', background: '#333' }}>
                    <h3>Status: <span style={{ color: isRunning ? '#646cff' : status === 'error' ? '#ef4444' : '#22c55e' }}>{status.toUpperCase()}</span></h3>
                    {lastError && <p style={{ color: '#ef4444' }}>Error: {lastError}</p>}

                    <div style={{ marginTop: '1rem', marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center', justifyContent: 'center' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            From:
                            <input
                                type="date"
                                value={dateRange.from}
                                onChange={(e) => setDateRange({ ...dateRange, from: e.target.value })}
                                disabled={isRunning}
                                style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #555', background: '#222', color: '#fff' }}
                            />
                        </label>
                        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            To:
                            <input
                                type="date"
                                value={dateRange.to}
                                onChange={(e) => setDateRange({ ...dateRange, to: e.target.value })}
                                disabled={isRunning}
                                style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #555', background: '#222', color: '#fff' }}
                            />
                        </label>
                    </div>

                    <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                        <button onClick={handleStart} disabled={isRunning}>
                            {isRunning ? 'Syncing...' : 'Start Sync Now'}
                        </button>
                        {isRunning && (
                            <button onClick={handleStop} style={{ background: '#b91c1c' }}>
                                Stop Sync
                            </button>
                        )}
                    </div>
                </div>

                {isRunning && (
                    <>
                        <div style={{ marginTop: '2rem' }}>
                            <h2>Live View</h2>
                            {isWaitingOtp && <div style={{ background: '#eab308', color: 'black', padding: '0.5rem', marginBottom: '0.5rem', borderRadius: '4px' }}>⚠️ Please verify OTP on your mobile app!</div>}
                            <div style={{ border: '2px solid #666', borderRadius: '8px', overflow: 'hidden', height: '400px', width: '700px', background: '#000', margin: '0 auto' }}>
                                <img
                                    src="/api/stream"
                                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                                    alt="Live Stream"
                                />
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
        </>
    )
}

export default DashboardPage
