import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function SettingsPage() {
    const [formData, setFormData] = useState({
        tcb_username: '',
        tcb_password: '',
        actual_url: '',
        actual_password: '',
        actual_budget_id: '',
        actual_budget_password: '',
        mappings: []
    });
    const [actualAccounts, setActualAccounts] = useState([]);
    const [loadingAccounts, setLoadingAccounts] = useState(false);
    const [msg, setMsg] = useState('');
    const fileInputRef = useRef(null);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await axios.get('/api/settings/');
                const data = res.data;
                let parsedMappings = [];
                try {
                    const raw = JSON.parse(data.accounts_mapping || '[]');
                    parsedMappings = Array.isArray(raw)
                        ? raw
                        : Object.entries(raw).map(([tcbId, actualId]) => ({
                            id: actualId, name: 'Imported', arrangementIds: [tcbId]
                          }));
                } catch { /* ignore malformed mapping JSON */ }
                setFormData({
                    ...data,
                    actual_url: data.actual_url || '',
                    actual_password: data.actual_password || '',
                    actual_budget_id: data.actual_budget_id || '',
                    actual_budget_password: data.actual_budget_password || '',
                    mappings: parsedMappings
                });
            } catch (e) {
                console.error(e);
            }
        };
        fetchSettings();
    }, []);

    const fetchActualAccounts = async () => {
        setLoadingAccounts(true);
        try {
            const res = await axios.get('/api/actual/accounts');
            setActualAccounts(res.data.accounts || []);
        } catch (e) {
            setMsg('Error fetching Actual accounts: ' + (e.response?.data?.detail || e.message));
        } finally {
            setLoadingAccounts(false);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleMappingChange = (index, field, value) => {
        const updated = [...formData.mappings];
        if (field === 'arrangementIds') {
            updated[index][field] = value.split(',').map(s => s.trim());
        } else {
            updated[index][field] = value;
        }
        setFormData({ ...formData, mappings: updated });
    };

    const addMapping = () => {
        setFormData({
            ...formData,
            mappings: [...formData.mappings, { id: '', name: '', arrangementIds: [] }]
        });
    };

    const removeMapping = (index) => {
        const updated = [...formData.mappings];
        updated.splice(index, 1);
        setFormData({ ...formData, mappings: updated });
    };

    const handleImport = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (evt) => {
            try {
                const json = JSON.parse(evt.target.result);
                setFormData(prev => ({
                    ...prev,
                    tcb_username: json.tcb_username || prev.tcb_username,
                    tcb_password: json.tcb_password || prev.tcb_password,
                    actual_url: json.actual_url || prev.actual_url,
                    actual_password: json.actual_password || prev.actual_password,
                    actual_budget_id: json.actual_budget_id || prev.actual_budget_id,
                    actual_budget_password: json.actual_budget_password || prev.actual_budget_password,
                    mappings: json.mappings || prev.mappings
                }));
            } catch {
                setMsg('Error: Invalid JSON file');
            }
        };
        reader.readAsText(file);
        e.target.value = '';
    };

    const handleExport = () => {
        const blob = new Blob([JSON.stringify({
            tcb_username: formData.tcb_username,
            tcb_password: formData.tcb_password,
            actual_url: formData.actual_url,
            actual_password: formData.actual_password,
            actual_budget_id: formData.actual_budget_id,
            actual_budget_password: formData.actual_budget_password,
            mappings: formData.mappings
        }, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'tcb-actual-settings.json';
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await axios.post('/api/settings/', {
                tcb_username: formData.tcb_username,
                tcb_password: formData.tcb_password,
                actual_url: formData.actual_url,
                actual_password: formData.actual_password,
                actual_budget_id: formData.actual_budget_id,
                actual_budget_password: formData.actual_budget_password,
                accounts_mapping: JSON.stringify(formData.mappings)
            });
            setMsg('Settings saved.');
        } catch (err) {
            setMsg('Error: ' + (err.response?.data?.detail || err.message));
        }
    };

    const getArrangementsString = (arr) =>
        Array.isArray(arr) ? arr.join(', ') : (arr || '');

    const actualAccountLabel = (acc) => {
        const flags = [];
        if (acc.offbudget) flags.push('off-budget');
        if (acc.closed) flags.push('closed');
        return flags.length ? `${acc.name} (${flags.join(', ')})` : acc.name;
    };

    return (
        <div className="app-shell">
            <nav className="top-nav">
                <span className="top-nav-brand">TCB → Actual</span>
                <div className="top-nav-actions">
                    <button className="btn-ghost btn-sm" onClick={() => navigate('/')}>← Dashboard</button>
                </div>
            </nav>

            <main className="page-content">
                <div className="page-header">
                    <h1>Settings</h1>
                    <p>Techcombank and Actual Budget credentials</p>
                </div>

                <form onSubmit={handleSubmit}>
                    {/* Techcombank */}
                    <div className="card" style={{ marginBottom: '0.875rem' }}>
                        <h2>Techcombank</h2>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }} className="grid-2">
                            <div className="form-field">
                                <label className="field-label">Username</label>
                                <input
                                    className="input-modern"
                                    name="tcb_username"
                                    value={formData.tcb_username}
                                    onChange={handleChange}
                                    placeholder="TCB username"
                                />
                            </div>
                            <div className="form-field">
                                <label className="field-label">Password</label>
                                <input
                                    className="input-modern"
                                    type="password"
                                    name="tcb_password"
                                    value={formData.tcb_password}
                                    onChange={handleChange}
                                    placeholder="TCB password"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Actual Budget */}
                    <div className="card" style={{ marginBottom: '0.875rem' }}>
                        <h2>Actual Budget</h2>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem' }} className="grid-2">
                            <div className="form-field">
                                <label className="field-label">Server URL</label>
                                <input
                                    className="input-modern input-mono"
                                    name="actual_url"
                                    value={formData.actual_url}
                                    onChange={handleChange}
                                    placeholder="http://192.168.31.193:5006"
                                    required
                                />
                            </div>
                            <div className="form-field">
                                <label className="field-label">Server Password</label>
                                <input
                                    className="input-modern"
                                    type="password"
                                    name="actual_password"
                                    value={formData.actual_password}
                                    onChange={handleChange}
                                    required
                                />
                            </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.875rem', marginTop: '0.875rem' }} className="grid-2">
                            <div className="form-field">
                                <label className="field-label">Budget Sync ID</label>
                                <input
                                    className="input-modern input-mono"
                                    name="actual_budget_id"
                                    value={formData.actual_budget_id}
                                    onChange={handleChange}
                                    placeholder="found in Settings → Advanced"
                                    required
                                />
                            </div>
                            <div className="form-field">
                                <label className="field-label">Budget Password</label>
                                <input
                                    className="input-modern"
                                    type="password"
                                    name="actual_budget_password"
                                    value={formData.actual_budget_password || ''}
                                    onChange={handleChange}
                                    placeholder="Leave empty if the budget is not encrypted"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Account Mappings */}
                    <div className="card" style={{ marginBottom: '0.875rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <h2 style={{ margin: 0 }}>Account Mappings</h2>
                            <div style={{ display: 'flex', gap: '0.375rem' }}>
                                <button
                                    type="button"
                                    className="btn-ghost btn-sm"
                                    onClick={fetchActualAccounts}
                                    disabled={loadingAccounts}
                                >
                                    {loadingAccounts ? 'Loading...' : 'Fetch Actual Accounts'}
                                </button>
                                <button type="button" className="btn-ghost btn-sm" onClick={addMapping}>
                                    + Add
                                </button>
                            </div>
                        </div>

                        <p className="field-hint" style={{ marginBottom: '0.875rem' }}>
                            Save the Actual credentials above first — accounts are read using the saved settings.
                        </p>

                        {actualAccounts.length > 0 && (
                            <div className="alert alert-info" style={{ marginBottom: '0.875rem' }}>
                                {actualAccounts.length} Actual account{actualAccounts.length !== 1 ? 's' : ''} loaded — select from dropdown below
                            </div>
                        )}

                        {formData.mappings.length === 0 && (
                            <div style={{
                                padding: '2rem', textAlign: 'center',
                                color: 'var(--text-muted)', fontSize: '0.8125rem',
                                border: '1px dashed var(--border)', borderRadius: '8px'
                            }}>
                                No mappings yet
                            </div>
                        )}

                        {formData.mappings.map((m, i) => (
                            <div key={i} style={{
                                background: 'rgba(255,255,255,0.02)',
                                border: '1px solid var(--border)',
                                borderRadius: '8px',
                                padding: '0.875rem',
                                marginBottom: '0.625rem'
                            }}>
                                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', alignItems: 'center' }}>
                                    <input
                                        className="input-modern"
                                        value={m.name}
                                        onChange={(e) => handleMappingChange(i, 'name', e.target.value)}
                                        placeholder="Account name"
                                        style={{ flex: 1 }}
                                    />
                                    <button
                                        type="button"
                                        className="btn-danger btn-sm"
                                        onClick={() => removeMapping(i)}
                                    >
                                        Remove
                                    </button>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }} className="grid-2">
                                    <div className="form-field">
                                        <label className="field-label">Actual Account</label>
                                        {actualAccounts.length > 0 ? (
                                            <select
                                                className="input-modern"
                                                value={m.id}
                                                onChange={(e) => {
                                                    const acc = actualAccounts.find(a => a.id === e.target.value);
                                                    const updated = [...formData.mappings];
                                                    updated[i].id = e.target.value;
                                                    if (acc && !updated[i].name) updated[i].name = acc.name;
                                                    setFormData({ ...formData, mappings: updated });
                                                }}
                                            >
                                                <option value="">Select account...</option>
                                                {actualAccounts.map(acc => (
                                                    <option key={acc.id} value={acc.id}>
                                                        {actualAccountLabel(acc)}
                                                    </option>
                                                ))}
                                            </select>
                                        ) : (
                                            <input
                                                className="input-modern input-mono"
                                                value={m.id}
                                                onChange={(e) => handleMappingChange(i, 'id', e.target.value)}
                                                placeholder="Actual account UUID"
                                            />
                                        )}
                                    </div>
                                    <div className="form-field">
                                        <label className="field-label">TCB Arrangement IDs</label>
                                        <input
                                            className="input-modern input-mono"
                                            value={getArrangementsString(m.arrangementIds)}
                                            onChange={(e) => handleMappingChange(i, 'arrangementIds', e.target.value)}
                                            placeholder="comma separated IDs"
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {msg && (
                        <div className={`alert ${msg.includes('Error') ? 'alert-error' : 'alert-success'}`}
                            style={{ marginBottom: '0.875rem' }}>
                            {msg}
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                        <input
                            type="file"
                            accept=".json"
                            ref={fileInputRef}
                            onChange={handleImport}
                            style={{ display: 'none' }}
                        />
                        <button type="button" className="btn-ghost btn-sm" onClick={() => fileInputRef.current?.click()}>
                            Import JSON
                        </button>
                        <button type="button" className="btn-ghost btn-sm" onClick={handleExport}>
                            Export JSON
                        </button>
                        <button type="submit">Save Settings</button>
                    </div>
                </form>
            </main>
        </div>
    );
}
