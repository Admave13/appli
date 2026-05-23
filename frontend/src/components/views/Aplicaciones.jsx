import React, { useState, useEffect } from 'react';
import './Aplicaciones.css';

const STATUS_OPTIONS = [
  "Enviada",
  "Esperando respuesta",
  "Entrevista",
  "Prueba tecnica",
  "Finalizada"
];

export default function Aplicaciones() {
  const [applications, setApplications] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [filter, setFilter] = useState('Todas');
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  
  // Estado del formulario
  const [formData, setFormData] = useState({
    company_id: '',
    company_name: '',
    company_logo: '',
    position: '',
    status: 'Enviada',
    applied_at: new Date().toISOString().split('T')[0],
    event_date: ''
  });

  useEffect(() => {
    fetchApplications();
    fetchCompanies();
  }, []);

  const fetchApplications = async () => {
    const res = await fetch('/api/applications');
    const data = await res.json();
    setApplications(data);
  };

  const fetchCompanies = async () => {
    const res = await fetch('/api/companies');
    const data = await res.json();
    setCompanies(data);
  };

  const openModal = (app = null) => {
    if (app) {
      setEditingId(app.id);
      setFormData({
        company_id: app.company_id || 'new',
        company_name: app.company_name,
        company_logo: app.company_logo,
        position: app.position,
        status: app.status,
        applied_at: app.applied_at,
        event_date: app.event_date || ''
      });
    } else {
      setEditingId(null);
      setFormData({
        company_id: 'new',
        company_name: '',
        company_logo: '',
        position: '',
        status: 'Enviada',
        applied_at: new Date().toISOString().split('T')[0],
        event_date: ''
      });
    }
    setIsModalOpen(true);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    
    // Lógica inteligente de empresas
    let payload = { ...formData };
    if (payload.company_id && payload.company_id !== 'new') {
      const selectedCompany = companies.find(c => c.id === parseInt(payload.company_id));
      if (selectedCompany) {
        payload.company_name = selectedCompany.name;
        payload.company_logo = selectedCompany.logo_path;
        payload.company_id = selectedCompany.id;
      }
    } else {
      payload.company_id = null; // Empresa manual
    }

    const method = editingId ? 'PUT' : 'POST';
    const url = editingId ? `/api/applications/${editingId}` : '/api/applications';

    await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    setIsModalOpen(false);
    fetchApplications();
  };

  const handleDelete = async (id) => {
    if (!confirm("¿Eliminar esta aplicación?")) return;
    await fetch(`/api/applications/${id}`, { method: 'DELETE' });
    setIsModalOpen(false);
    fetchApplications();
  };

  const getDaysAgo = (dateStr) => {
    const applyDate = new Date(dateStr);
    const today = new Date();
    const diffTime = Math.abs(today - applyDate);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays === 0 ? 'Hoy' : `Hace ${diffDays} días`;
  };

  const filteredApps = filter === 'Todas' 
    ? applications 
    : applications.filter(a => a.status === filter);

  return (
    <div className="view-container">
      <div className="view-header">
        <h1>Mis Aplicaciones</h1>
        <button className="btn-primary" onClick={() => openModal()}>+ Nueva Aplicación</button>
      </div>

      <div className="filters">
        <button className={filter === 'Todas' ? 'active' : ''} onClick={() => setFilter('Todas')}>Todas</button>
        {STATUS_OPTIONS.map(status => (
          <button key={status} className={filter === status ? 'active' : ''} onClick={() => setFilter(status)}>
            {status}
          </button>
        ))}
      </div>

      <div className="applications-grid">
        {filteredApps.map(app => (
          <div className="app-card" key={app.id}>
            <div className="app-card-header">
              <div className="company-info">
                {app.company_logo ? (
                   <img src={app.company_logo} alt="logo" className="app-logo" />
                ) : (
                   <div className="app-logo-placeholder">{app.company_name.charAt(0)}</div>
                )}
                <div>
                  <h3>{app.position}</h3>
                  <p className="company-name">{app.company_name}</p>
                </div>
              </div>
              <button className="btn-icon" onClick={() => openModal(app)}>✎</button>
            </div>
            
            <div className="app-card-body">
              <span className={`status-badge status-${app.status.replace(/\s+/g, '-').toLowerCase()}`}>
                {app.status}
              </span>
              <span className="time-ago">{getDaysAgo(app.applied_at)}</span>
            </div>

            {(app.status === 'Entrevista' || app.status === 'Prueba tecnica') && app.event_date && (
              <div className="app-event-info">
                <strong>🗓 {app.status}:</strong> {new Date(app.event_date).toLocaleString([], {dateStyle: 'short', timeStyle: 'short'})}
              </div>
            )}
          </div>
        ))}
      </div>

      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>{editingId ? 'Editar Aplicación' : 'Nueva Aplicación'}</h2>
            <form onSubmit={handleSave}>
              <div className="form-group">
                <label>Posición</label>
                <input required type="text" value={formData.position} onChange={e => setFormData({...formData, position: e.target.value})} />
              </div>

              <div className="form-group">
                <label>Empresa</label>
                <select 
                  value={formData.company_id} 
                  onChange={e => setFormData({...formData, company_id: e.target.value})}
                >
                  <option value="new">-- Añadir manualmente (Sin guardar en empresas) --</option>
                  {companies.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>

              {formData.company_id === 'new' && (
                <div className="inline-group">
                  <input required type="text" placeholder="Nombre empresa" value={formData.company_name} onChange={e => setFormData({...formData, company_name: e.target.value})} />
                  <input type="text" placeholder="URL Foto (Opcional)" value={formData.company_logo} onChange={e => setFormData({...formData, company_logo: e.target.value})} />
                </div>
              )}

              <div className="inline-group">
                <div className="form-group">
                  <label>Progreso</label>
                  <select value={formData.status} onChange={e => setFormData({...formData, status: e.target.value})}>
                    {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Fecha de envío</label>
                  <input required type="date" value={formData.applied_at} onChange={e => setFormData({...formData, applied_at: e.target.value})} />
                </div>
              </div>

              {(formData.status === 'Entrevista' || formData.status === 'Prueba tecnica') && (
                <div className="form-group animate-fade">
                  <label>Fecha y hora del evento</label>
                  <input type="datetime-local" value={formData.event_date} onChange={e => setFormData({...formData, event_date: e.target.value})} />
                </div>
              )}

              <div className="modal-actions">
                {editingId && (
                   <button type="button" className="btn-danger mr-auto" onClick={() => handleDelete(editingId)}>Eliminar</button>
                )}
                <button type="button" className="btn-secondary" onClick={() => setIsModalOpen(false)}>Cancelar</button>
                <button type="submit" className="btn-primary">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}