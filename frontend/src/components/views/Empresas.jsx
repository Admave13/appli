import { useState, useEffect } from 'react';
import './Empresas.css';

// ── API helpers ──────────────────────────────────────────────────────────────
const api = {
  getCompanies: () => fetch('/api/companies').then(r => r.json()),
  saveCompany: (data) => fetch('/api/companies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => r.json()),
  // NUEVO: Método para actualizar (Editar)
  updateCompany: (id, data) => fetch(`/api/companies/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => r.json()),
  // NUEVO: Método para eliminar
  deleteCompany: (id) => fetch(`/api/companies/${id}`, {
    method: 'DELETE'
  }),
  visitCompany: (id) => fetch(`/api/companies/${id}/visit`, {
    method: 'PUT'
  }).then(r => r.json()),
};

export default function Empresas() {
  const [companies, setCompanies] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  // NUEVO: Estado para saber qué empresa estamos editando (null = modo creación)
  const [editingId, setEditingId] = useState(null); 
  const [formData, setFormData] = useState({ name: '', url: '', logo_path: '', notes: '' });

  const loadCompanies = () => {
    api.getCompanies().then(data => setCompanies(data || []));
  };

  useEffect(() => {
    loadCompanies();
  }, []);

  const parseDate = (dateStr) => {
    if (!dateStr) return 0;
    const [datePart, timePart] = dateStr.split(' ');
    if (!datePart || !timePart) return 0;
    const [day, month, year] = datePart.split('/');
    const [hour, minute] = timePart.split(':');
    return new Date(year, month - 1, day, hour, minute).getTime();
  };

  const sortedCompanies = [...companies].sort((a, b) => parseDate(b.last_visited) - parseDate(a.last_visited));

  const handleCardClick = async (company) => {
    if (!company.url) return;
    window.open(company.url, '_blank');
    await api.visitCompany(company.id);
    loadCompanies();
  };

  // NUEVO: Función para abrir el modal en modo creación
  const openCreateModal = () => {
    setEditingId(null);
    setFormData({ name: '', url: '', logo_path: '', notes: '' });
    setIsModalOpen(true);
  };

  // NUEVO: Función para abrir el modal en modo edición
  const handleEditClick = (e, company) => {
    e.stopPropagation(); // Evita que se abra la URL de la empresa
    setEditingId(company.id);
    setFormData({
      name: company.name || '',
      url: company.url || '',
      logo_path: company.logo_path || '',
      notes: company.notes || ''
    });
    setIsModalOpen(true);
  };

  // NUEVO: Función para eliminar
  const handleDeleteClick = async (e, id) => {
    e.stopPropagation(); // Evita que se abra la URL de la empresa
    if (window.confirm('¿Estás seguro de que quieres eliminar esta empresa?')) {
      await api.deleteCompany(id);
      loadCompanies();
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    // MODIFICADO: Decide si crear o actualizar dependiendo de si existe editingId
    if (editingId) {
      await api.updateCompany(editingId, formData);
    } else {
      await api.saveCompany(formData);
    }
    
    setIsModalOpen(false);
    setEditingId(null);
    setFormData({ name: '', url: '', logo_path: '', notes: '' });
    loadCompanies();
  };

  return (
    <div className="empresas-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Directorio de Empresas</h1>
          <p className="page-subtitle">Tus empresas guardadas, ordenadas por tu última visita.</p>
        </div>
        {/* MODIFICADO: Llama a openCreateModal */}
        <button className="btn-primary" onClick={openCreateModal}>
          + Añadir Empresa
        </button>
      </div>

      <div className="empresas-grid">
        {sortedCompanies.map(company => (
          <div 
            key={company.id} 
            className="empresa-card" 
            onClick={() => handleCardClick(company)}
          >
            {/* NUEVO: Botones de acción flotantes */}
            <div className="empresa-actions">
              <button 
                className="btn-icon btn-edit" 
                title="Editar"
                onClick={(e) => handleEditClick(e, company)}
              >
                ✏️
              </button>
              <button 
                className="btn-icon btn-delete" 
                title="Eliminar"
                onClick={(e) => handleDeleteClick(e, company.id)}
              >
                🗑️
              </button>
            </div>

            <div className="empresa-image-container">
              {company.logo_path ? (
                <img src={company.logo_path} alt={`${company.name} logo`} className="empresa-logo" />
              ) : (
                <div className="empresa-placeholder">
                  {company.name.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
            
            <div className="empresa-info">
              <h3 className="empresa-name">{company.name}</h3>
              {company.notes && <span className="empresa-type">{company.notes}</span>}
              <div className="empresa-meta">
                <small>Última visita:</small>
                <small className="empresa-date">{company.last_visited || 'Nunca'}</small>
              </div>
            </div>
          </div>
        ))}
        {companies.length === 0 && (
          <p style={{ color: 'var(--text-secondary)' }}>No hay empresas guardadas aún.</p>
        )}
      </div>

      {isModalOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            {/* MODIFICADO: El título cambia según el modo */}
            <h2>{editingId ? 'Editar Empresa' : 'Añadir Nueva Empresa'}</h2>
            <form onSubmit={handleSave}>
              <div className="form-group">
                <label>Nombre de la Empresa *</label>
                <input 
                  type="text" 
                  required
                  value={formData.name} 
                  onChange={e => setFormData({...formData, name: e.target.value})} 
                  placeholder="Ej. Acme Corp"
                />
              </div>
              <div className="form-group">
                <label>URL de la Empresa</label>
                <input 
                  type="url" 
                  value={formData.url} 
                  onChange={e => setFormData({...formData, url: e.target.value})} 
                  placeholder="https://..."
                />
              </div>
              <div className="form-group">
                <label>URL del Logo (Imagen)</label>
                <input 
                  type="url" 
                  value={formData.logo_path} 
                  onChange={e => setFormData({...formData, logo_path: e.target.value})} 
                  placeholder="https://..."
                />
              </div>
              <div className="form-group">
                <label>Tipo de Empresa</label>
                <input 
                  type="text" 
                  value={formData.notes} 
                  onChange={e => setFormData({...formData, notes: e.target.value})} 
                  placeholder="Ej. Startup, Consultora, Producto..."
                />
              </div>
              
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setIsModalOpen(false)}>Cancelar</button>
                {/* MODIFICADO: El texto del botón cambia */}
                <button type="submit" className="btn-primary">
                  {editingId ? 'Actualizar' : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}