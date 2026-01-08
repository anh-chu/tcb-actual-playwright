import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
    const [isRegister, setIsRegister] = useState(false);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login, register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            if (isRegister) {
                await register(username, password);
            } else {
                await login(username, password);
            }
            navigate('/');
        } catch (err) {
            setError(err.response?.data?.detail || 'Authentication failed');
        }
    };

    return (
        <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
            <div className="glass-card" style={{ width: '100%', maxWidth: '400px', margin: '2rem' }}>
                <h2 style={{ textAlign: 'center', marginBottom: '3rem', fontSize: '2.4rem' }}>
                    {isRegister ? 'Join Actual Sync' : 'Welcome Back'}
                </h2>

                {error && (
                    <div className="status-badge status-error" style={{ width: '100%', marginBottom: '1.5rem', justifyContent: 'center', borderRadius: '12px' }}>
                        {error}
                    </div>
                )}
                <form onSubmit={handleSubmit}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginBottom: '2rem' }}>
                        <div className="form-group" style={{ marginBottom: '0' }}>
                            <label style={{ marginBottom: '0.75rem', fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-muted)' }}>Username</label>
                            <input
                                type="text"
                                className="input-modern"
                                value={username}
                                onChange={e => setUsername(e.target.value)}
                                placeholder="Enter your username"
                                required
                            />
                        </div>
                        <div className="form-group" style={{ marginBottom: '0' }}>
                            <label style={{ marginBottom: '0.75rem', fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-muted)' }}>Password</label>
                            <input
                                type="password"
                                className="input-modern"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                placeholder="Enter your password"
                                required
                            />
                        </div>
                    </div>

                    <button type="submit" style={{ width: '100%', padding: '1.1rem', fontSize: '1.1rem' }}>
                        {isRegister ? 'Create Account' : 'Sign In'}
                    </button>
                </form>

                <div style={{ marginTop: '2rem', textAlign: 'center' }}>
                    <span
                        style={{ cursor: 'pointer', fontSize: '0.9rem', color: 'var(--text-muted)', transition: 'color 0.2s' }}
                        onClick={() => { setError(''); setIsRegister(!isRegister); }}
                        onMouseOver={e => e.target.style.color = 'var(--text-main)'}
                        onMouseOut={e => e.target.style.color = 'var(--text-muted)'}
                    >
                        {isRegister ? 'Already have an account? Login' : 'Need an account? Create one'}
                    </span>
                </div>
            </div>
        </div>
    );
}
