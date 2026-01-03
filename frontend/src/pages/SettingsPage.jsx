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
        <div style={{ maxWidth: '900px', margin: '0 auto', padding: '2rem' }}>
            <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem' }}>
                    <h2 style={{ margin: 0 }}>Configuration</h2>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <input
                            type="file"
                            ref={fileInputRef}
                            style={{ display: 'none' }}
                            onChange={handleImport}
                            accept=".json"
                        />
                        <button type="button" onClick={() => fileInputRef.current.click()} style={{ background: '#0891b2' }}>
                            Import JSON
                        </button>
                        <button type="button" onClick={handleExport} style={{ background: '#4f46e5' }}>
                            Export JSON
                        </button>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>

                    <h3 style={{ color: '#aaa', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px', marginTop: '1.5rem' }}>
                        Techcombank Credentials
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div className="form-group">
                            <label>Username</label>
                            <input name="tcb_username" value={formData.tcb_username} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>Password</label>
                            <input type="password" name="tcb_password" value={formData.tcb_password} onChange={handleChange} required />
                        </div>
                    </div>

                    <h3 style={{ color: '#aaa', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px', marginTop: '1.5rem' }}>
                        Actual Budget
                    </h3>
                    <div className="form-group">
                        <label>Server URL</label>
                        <input name="actual_url" value={formData.actual_url} onChange={handleChange} placeholder="http://your-server:5006" required />
                    </div>
                    <div className="form-group">
                        <label>Server Password</label>
                        <input type="password" name="actual_password" value={formData.actual_password} onChange={handleChange} required />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div className="form-group">
                            <label>Budget ID</label>
                            <input name="actual_budget_id" value={formData.actual_budget_id} onChange={handleChange} required />
                        </div>
                        <div className="form-group">
                            <label>Budget Encryption Password (Optional)</label>
                            <input type="password" name="actual_budget_password" value={formData.actual_budget_password || ''} onChange={handleChange} />
                        </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '2rem' }}>
                        <h3 style={{ color: '#aaa', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '1px', margin: 0 }}>
                            Account Mapping
                        </h3>
                        <button type="button" onClick={addMapping} style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem', background: '#22c55e' }}>
                            + Add Account
                        </button>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
                        {formData.mappings.map((m, i) => (
                            <div key={i} style={{
                                background: 'rgba(0,0,0,0.2)',
                                padding: '1rem',
                                borderRadius: '8px',
                                border: '1px solid #444'
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                    <input
                                        value={m.name}
                                        onChange={(e) => handleMappingChange(i, 'name', e.target.value)}
                                        placeholder="Account Name (e.g. TCB Spend)"
                                        style={{ fontWeight: 'bold', border: 'none', background: 'transparent', padding: 0, width: '50%' }}
                                    />
                                    <button type="button" onClick={() => removeMapping(i)} style={{ background: 'transparent', color: '#ef4444', padding: 0, border: 'none', fontSize: '1.2rem' }}>
                                        &times;
                                    </button>
                                </div>

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1rem' }}>
                                    <div>
                                        <label style={{ fontSize: '0.8rem' }}>Actual Account UUID</label>
                                        <input
                                            value={m.id}
                                            onChange={(e) => handleMappingChange(i, 'id', e.target.value)}
                                            placeholder="UUID form Actual"
                                            style={{ padding: '0.4rem', fontSize: '0.9rem' }}
                                        />
                                    </div>
                                    <div>
                                        <label style={{ fontSize: '0.8rem' }}>TCB Account/Arrangement IDs (comma separated)</label>
                                        <input
                                            value={getArrangmentsString(m.arrangementIds)}
                                            onChange={(e) => handleMappingChange(i, 'arrangementIds', e.target.value)}
                                            placeholder="0ce41c5d-..."
                                            style={{ padding: '0.4rem', fontSize: '0.9rem', fontFamily: 'monospace' }}
                                        />
                                    </div>
                                </div>
                            </div>
                        ))}
                        {formData.mappings.length === 0 && (
                            <div style={{ textAlign: 'center', color: '#666', padding: '2rem', border: '2px dashed #444', borderRadius: '8px' }}>
                                No accounts mapped. Click "Add Account" or Import JSON.
                            </div>
                        )}
                    </div>

                    {msg && (
                        <div style={{
                            marginTop: '1.5rem',
                            padding: '0.75rem',
                            borderRadius: '8px',
                            background: msg.includes('Error') ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)',
                            color: msg.includes('Error') ? '#fca5a5' : '#86efac',
                            border: `1px solid ${msg.includes('Error') ? '#ef4444' : '#22c55e'} `
                        }}>
                            {msg}
                        </div>
                    )}

                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '2rem' }}>
                        <button type="button" onClick={() => navigate('/')} style={{ background: 'transparent', border: '1px solid #666' }}>Cancel</button>
                        <button type="submit">Save Changes</button>
                    </div>
                </form>
            </div>
        </div>
    );
}
