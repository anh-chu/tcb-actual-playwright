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
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem'
        }}>
            <div style={{ width: '100%', maxWidth: '340px' }}>
                <div style={{ marginBottom: '1.75rem' }}>
                    <h1 style={{ fontSize: '1.1rem' }}>
                        {isRegister ? 'Create account' : 'Sign in'}
                    </h1>
                    <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                        TCB → Actual sync
                    </p>
                </div>

                {error && (
                    <div className="alert alert-error" style={{ marginBottom: '1rem' }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
                        <div className="form-field">
                            <label className="field-label">Username</label>
                            <input
                                className="input-modern"
                                type="text"
                                value={username}
                                onChange={e => setUsername(e.target.value)}
                                placeholder="username"
                                required
                            />
                        </div>
                        <div className="form-field">
                            <label className="field-label">Password</label>
                            <input
                                className="input-modern"
                                type="password"
                                value={password}
                                onChange={e => setPassword(e.target.value)}
                                placeholder="password"
                                required
                            />
                        </div>
                    </div>

                    <button type="submit" style={{ width: '100%', height: '38px' }}>
                        {isRegister ? 'Create account' : 'Sign in'}
                    </button>
                </form>

                <p style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span
                        style={{ cursor: 'pointer', textDecoration: 'underline', textDecorationColor: 'transparent' }}
                        onMouseOver={e => e.target.style.textDecorationColor = 'var(--text-muted)'}
                        onMouseOut={e => e.target.style.textDecorationColor = 'transparent'}
                        onClick={() => { setError(''); setIsRegister(!isRegister); }}
                    >
                        {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Create one"}
                    </span>
                </p>
            </div>
        </div>
    );
}
