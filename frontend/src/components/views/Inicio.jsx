import React, { useState, useEffect } from 'react';
import './Inicio.css';

const STATUS_PRIORITY = ['Entrevista', 'Prueba tecnica', 'Esperando respuesta', 'Enviada', 'Finalizada'];

const STATUS_LABELS = {
  'Enviada': 'Enviada',
  'Esperando respuesta': 'En proceso',
  'Entrevista': 'Entrevista',
  'Prueba tecnica': 'Prueba técnica',
  'Finalizada': 'Finalizada',
};

const STATUS_COLORS = {
  'Enviada':              'status-enviada',
  'Esperando respuesta':  'status-proceso',
  'Entrevista':           'status-entrevista',
  'Prueba tecnica':       'status-prueba',
  'Finalizada':           'status-finalizada',
};

export default function Inicio({ onNavigate }) {
  const [applications, setApplications] = useState([]);
  const [companies, setCompanies]       = useState([]);
  const [loading, setLoading]           = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('/api/applications').then(r => r.json()),
      fetch('/api/companies').then(r => r.json()),
    ]).then(([apps, comps]) => {
      setApplications(apps);
      setCompanies(comps);
      setLoading(false);
    });
  }, []);

  /* ── Stats ── */
  const total         = applications.length;
  const enProceso     = applications.filter(a => a.status === 'Esperando respuesta').length;
  const entrevistas   = applications.filter(a => a.status === 'Entrevista').length;
  const pruebas       = applications.filter(a => a.status === 'Prueba tecnica').length;
  const ofertas       = applications.filter(a => a.status === 'Finalizada').length;

  /* ── Sorted applications ──
     1. Entrevista / Prueba tecnica con event_date → ordenadas por event_date ASC
     2. El resto → ordenadas por applied_at DESC  */
  const sortedApps = React.useMemo(() => {
    const withEvent = applications
      .filter(a => (a.status === 'Entrevista' || a.status === 'Prueba tecnica') && a.event_date)
      .sort((a, b) => new Date(a.event_date) - new Date(b.event_date));

    const rest = applications
      .filter(a => !((a.status === 'Entrevista' || a.status === 'Prueba tecnica') && a.event_date))
      .sort((a, b) => new Date(b.applied_at) - new Date(a.applied_at));

    return [...withEvent, ...rest].slice(0, 8);
  }, [applications]);

  /* ── 5 empresas visitadas hace más tiempo ── */
  const oldestVisited = React.useMemo(() => {
    return [...companies]
      .filter(c => c.last_visited)
      .sort((a, b) => new Date(a.last_visited) - new Date(b.last_visited))
      .slice(0, 5);
  }, [companies]);

  /* ── Helpers ── */
  const getDaysAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = Math.floor((new Date() - new Date(dateStr)) / 86400000);
    if (diff === 0) return 'Hoy';
    if (diff === 1) return 'Ayer';
    return `Hace ${diff} días`;
  };

  const formatEventDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleString('es-ES', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  };

  const formatLastVisited = (dateStr) => {
    if (!dateStr) return 'Nunca';
    const diff = Math.floor((new Date() - new Date(dateStr)) / 86400000);
    if (diff === 0) return 'Hoy';
    if (diff === 1) return 'Ayer';
    return `Hace ${diff} días`;
  };

  const isUrgent = (app) => {
    if (!app.event_date) return false;
    const diff = Math.floor((new Date(app.event_date) - new Date()) / 86400000);
    return diff >= 0 && diff <= 2;
  };

  if (loading) {
    return (
      <div className="inicio-loading">
        <div className="loading-dots">
          <span /><span /><span />
        </div>
      </div>
    );
  }

  return (
    <div className="inicio-container">

      {/* ── Header ── */}
      <div className="inicio-header">
        <div>
          <h1 className="inicio-title">¡Hola, Alex! <span className="wave">👋</span></h1>
          <p className="inicio-subtitle">Aquí tienes un resumen de tu actividad.</p>
        </div>
      </div>

      {/* ── Stats row ── */}
      <div className="stats-row">
        <div className="stat-card stat-total">
          <span className="stat-number">{total}</span>
          <span className="stat-label">Aplicaciones<br/>Total enviadas</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{enProceso}</span>
          <span className="stat-label">En proceso</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{entrevistas + pruebas}</span>
          <span className="stat-label">Entrevistas<br/>Programadas</span>
        </div>
        <div className="stat-card">
          <span className="stat-number">{ofertas}</span>
          <span className="stat-label">Finalizadas</span>
        </div>
      </div>

      {/* ── Main grid ── */}
      <div className="inicio-grid">

        {/* ── Actividad reciente ── */}
        <section className="card actividad-card">
          <div className="card-header">
            <h2>Actividad reciente</h2>
            <button className="link-btn" onClick={() => onNavigate?.('aplicaciones')}>
              Ver todas mis aplicaciones →
            </button>
          </div>

          <div className="activity-list">
            {sortedApps.length === 0 && (
              <p className="empty-msg">Aún no tienes aplicaciones. ¡Empieza a aplicar!</p>
            )}
            {sortedApps.map(app => (
              <div className={`activity-item ${isUrgent(app) ? 'activity-item--urgent' : ''}`} key={app.id}>
                <div className="activity-logo">
                  {app.company_logo
                    ? <img src={app.company_logo} alt={app.company_name} />
                    : <div className="logo-placeholder">{(app.company_name || '?').charAt(0).toUpperCase()}</div>
                  }
                </div>
                <div className="activity-info">
                  <span className="activity-position">{app.position}</span>
                  <span className="activity-company">{app.company_name}</span>
                  {(app.status === 'Entrevista' || app.status === 'Prueba tecnica') && app.event_date && (
                    <span className="activity-event">
                      🗓 {formatEventDate(app.event_date)}
                    </span>
                  )}
                  {!(app.status === 'Entrevista' || app.status === 'Prueba tecnica') && (
                    <span className="activity-time">{getDaysAgo(app.applied_at)}</span>
                  )}
                </div>
                <span className={`badge ${STATUS_COLORS[app.status]}`}>
                  {STATUS_LABELS[app.status]}
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* ── Empresas pendientes de visitar ── */}
        <section className="card empresas-card">
          <div className="card-header">
            <h2>Empresas sin revisar</h2>
            <button className="link-btn" onClick={() => onNavigate?.('empresas')}>
              Ver empresas →
            </button>
          </div>

          {oldestVisited.length === 0 ? (
            <p className="empty-msg">No hay empresas guardadas con visitas registradas.</p>
          ) : (
            <div className="empresas-list">
              {oldestVisited.map((company, i) => (
                <div className="empresa-item" key={company.id}>
                  <span className="empresa-rank">#{i + 1}</span>
                  <div className="empresa-logo">
                    {company.logo_path
                      ? <img src={company.logo_path} alt={company.name} />
                      : <div className="logo-placeholder logo-placeholder--sm">{company.name.charAt(0).toUpperCase()}</div>
                    }
                  </div>
                  <div className="empresa-info">
                    <span className="empresa-name">{company.name}</span>
                    <span className="empresa-visited">Última visita: {formatLastVisited(company.last_visited)}</span>
                  </div>
                  {company.url && (
                    <a
                      href={company.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="empresa-visit-btn"
                      title="Visitar"
                    >↗</a>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

      </div>
    </div>
  );
}