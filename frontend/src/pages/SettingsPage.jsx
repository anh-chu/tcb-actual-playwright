import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function SettingsPage() {
    const [formData, setFormData] = useState({
        // ... (rest of the file is fine, just removing the wrapper)
        tcb_username: '',
        tcb_password: '',
        actual_url: '',
        actual_password: '',
        actual_budget_id: '',
        actual_budget_password: '',
        // Mappings will be parsed into this array
        mappings: []
    });
    const [msg, setMsg] = useState('');
    const fileInputRef = useRef(null);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const res = await axios.get('/api/settings/');
                const data = res.data;

                // Parse the stored JSON string for mappings
                let parsedMappings = [];
                try {
                    const raw = JSON.parse(data.accounts_mapping || '[]');
                    if (Array.isArray(raw)) {
                        parsedMappings = raw;
                    } else {
                        // Convert legacy flat dict to list format
                        parsedMappings = Object.entries(raw).map(([tcbId, actualId]) => ({
                            id: actualId,
                            name: 'Legacy Import',
                            arrangementIds: [tcbId]
                        }));
                    }
                } catch (e) {
                    console.error("Failed to parse mappings", e);
                }

                setFormData({
                    ...data,
                    mappings: parsedMappings
                });
            } catch (e) {
                console.error(e);
            }
        };
        fetchSettings();
    }, []);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleMappingChange = (index, field, value) => {
        const newMappings = [...formData.mappings];
        if (field === 'arrangementIds') {
            // split by comma for UI editing, but store as array
            newMappings[index][field] = value.split(',').map(s => s.trim());
        } else {
            newMappings[index][field] = value;
        }
        setFormData({ ...formData, mappings: newMappings });
    };

    const addMapping = () => {
        setFormData({
            ...formData,
            mappings: [...formData.mappings, { id: '', name: 'New Account', arrangementIds: [] }]
        });
    };

    const removeMapping = (index) => {
        const newMappings = [...formData.mappings];
        newMappings.splice(index, 1);
        setFormData({ ...formData, mappings: newMappings });
    };

    const handleImport = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (evt) => {
            try {
                const json = JSON.parse(evt.target.result);
                // Merge imported data
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
                setMsg('Configuration imported successfully!');
            } catch (err) {
                setMsg('Error parsing JSON file: ' + err.message);
            }
        };
        reader.readAsText(file);
        // Reset input
        e.target.value = null;
    };

    const handleExport = () => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(formData, null, 4));
        const downloadAnchorNode = document.createElement('a');
        downloadAnchorNode.setAttribute("href", dataStr);
        downloadAnchorNode.setAttribute("download", "tcb_actual_config.json");
        document.body.appendChild(downloadAnchorNode);
        downloadAnchorNode.click();
        downloadAnchorNode.remove();
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            // Prepare payload: convert mappings array back to JSON string for storage
            const payload = {
                ...formData,
                accounts_mapping: JSON.stringify(formData.mappings)
            };
            // Remove temporary mappings field from payload to match schema if necessary
            // But our schema in frontend is just constructing the object. 
            // The backend expects accounts_mapping string.

            await axios.post('/api/settings/', payload);
            setMsg('Settings saved successfully!');
            setTimeout(() => navigate('/'), 1500);
        } catch (e) {
            setMsg('Error saving settings: ' + (e.response?.data?.detail || e.message));
        }
    };

    // Helper to join array for display
    const getArrangmentsString = (arrIds) => {
        if (!arrIds) return "";
        return Array.isArray(arrIds) ? arrIds.join(', ') : arrIds;
    };

    return (
        <div className="container" style={{ maxWidth: '900px' }}>
            <div className="glass-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2.5rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '1.5rem' }}>
                    <h2 style={{ margin: 0 }}>Sync Configuration</h2>
                    <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <input
                            type="file"
                            ref={fileInputRef}
                            style={{ display: 'none' }}
                            onChange={handleImport}
                            accept=".json"
                        />
                        <button type="button" className="btn-secondary" style={{ padding: '0.5rem 1rem' }} onClick={() => fileInputRef.current.click()}>
                            Import JSON
                        </button>
                        <button type="button" className="btn-secondary" style={{ padding: '0.5rem 1rem' }} onClick={handleExport}>
                            Export JSON
                        </button>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>

                    <h3 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', marginTop: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ width: '8px', height: '8px', background: 'var(--primary)', borderRadius: '2px' }}></span>
                        Techcombank Credentials
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                        <div className="form-group">
                            <label>Username</label>
                            <input className="input-modern" name="tcb_username" value={formData.tcb_username} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>Password</label>
                            <input className="input-modern" type="password" name="tcb_password" value={formData.tcb_password} onChange={handleChange} required />
                        </div>
                    </div>

                    <h3 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', marginTop: '2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ width: '8px', height: '8px', background: 'var(--info)', borderRadius: '2px' }}></span>
                        Actual Budget Settings
                    </h3>
                    <div className="form-group">
                        <label>Server URL</label>
                        <input className="input-modern" name="actual_url" value={formData.actual_url} onChange={handleChange} placeholder="http://your-server:5006" required />
                    </div>
                    <div className="form-group">
                        <label>Server Password</label>
                        <input className="input-modern" type="password" name="actual_password" value={formData.actual_password} onChange={handleChange} required />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                        <div className="form-group">
                            <label>Budget ID</label>
                            <input className="input-modern" name="actual_budget_id" value={formData.actual_budget_id} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>Budget Encryption Password</label>
                            <input className="input-modern" type="password" name="actual_budget_password" value={formData.actual_budget_password || ''} onChange={handleChange} placeholder="Skip if not encrypted" />
                        </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '3rem', marginBottom: '1.5rem' }}>
                        <h3 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <span style={{ width: '8px', height: '8px', background: 'var(--success)', borderRadius: '2px' }}></span>
                            Account Mappings
                        </h3>
                        <button type="button" onClick={addMapping} style={{ fontSize: '0.8rem', padding: '0.5rem 1rem', background: 'var(--success)', border: 'none' }}>
                            + Add Account
                        </button>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {formData.mappings.map((m, i) => (
                            <div key={i} style={{
                                background: 'rgba(0,0,0,0.3)',
                                padding: '1.5rem',
                                borderRadius: '16px',
                                border: '1px solid var(--glass-border)',
                                position: 'relative'
                            }}>
                                <button type="button" onClick={() => removeMapping(i)} style={{ position: 'absolute', top: '1rem', right: '1rem', background: 'transparent', color: 'var(--error)', padding: '0.5rem', border: 'none', fontSize: '1.5rem', lineHeight: 1 }}>
                                    &times;
                                </button>

                                <div className="form-group" style={{ maxWidth: '70%' }}>
                                    <input
                                        value={m.name}
                                        onChange={(e) => handleMappingChange(i, 'name', e.target.value)}
                                        placeholder="Account Name (e.g. Spending)"
                                        className="input-modern"
                                        style={{ fontWeight: '700', fontSize: '1.1rem', border: 'none', background: 'transparent', padding: 0 }}
                                    />
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                                    <div>
                                        <label style={{ fontSize: '0.75rem', fontWeight: '700' }}>ACTUAL UUID</label>
                                        <input
                                            className="input-modern"
                                            value={m.id}
                                            onChange={(e) => handleMappingChange(i, 'id', e.target.value)}
                                            placeholder="Account ID from Actual"
                                            style={{ fontSize: '0.9rem' }}
                                        />
                                    </div>
                                    <div>
                                        <label style={{ fontSize: '0.75rem', fontWeight: '700' }}>TCB ARRANGEMENT IDs</label>
                                        <input
                                            className="input-modern"
                                            value={getArrangmentsString(m.arrangementIds)}
                                            onChange={(e) => handleMappingChange(i, 'arrangementIds', e.target.value)}
                                            placeholder="comma separated IDs"
                                            style={{ fontSize: '0.9rem', fontFamily: 'monospace' }}
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                        {formData.mappings.length === 0 && (
                            <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem', border: '2px dashed var(--glass-border)', borderRadius: '16px', background: 'rgba(255,255,255,0.02)' }}>
                                No account mappings found.
                            </div>
                        )}
                    </div>

                    {msg && (
                        <div style={{
                            marginTop: '2rem',
                            padding: '1rem',
                            borderRadius: '12px',
                            textAlign: 'center',
                            fontSize: '0.95rem',
                            fontWeight: '500',
                            background: msg.includes('Error') ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                            color: msg.includes('Error') ? 'var(--error)' : 'var(--success)',
                            border: `1px solid ${msg.includes('Error') ? 'var(--error)' : 'var(--success)'} `
                        }}>
                            {msg}
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '3rem' }}>
                        <button type="button" className="btn-secondary" onClick={() => navigate('/')} style={{ minWidth: '140px' }}>Back to Home</button>
                        <button type="submit" style={{ minWidth: '180px' }}>Save All Settings</button>
                    </div>
                </form>
            </div>
        </div>
    );
}
