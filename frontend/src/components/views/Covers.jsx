import { useState, useEffect } from 'react'
import './Covers.css'

// ── API helpers ───────────────────────────────────────────────────────────────

const api = {
  getCovers: () =>
    fetch('/api/covers').then(r => r.json()),

  generateCover: (data) =>
    fetch('/api/covers/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json()),

  updateCover: (id, data) =>
    fetch(`/api/covers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }).then(r => r.json()),

  deleteCover: (id) =>
    fetch(`/api/covers/${id}`, { method: 'DELETE' }).then(r => r.json()),

  downloadPdf: (id) =>
    fetch(`/api/covers/${id}/pdf`),
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="covers-empty">
      <div className="covers-empty-icon">✉️</div>
      <p className="covers-empty-text">Todavía no hay cover letters.</p>
      <p className="covers-empty-sub">Pulsa «Nueva Cover» para crear la primera.</p>
    </div>
  )
}

// ── Modal nueva cover ─────────────────────────────────────────────────────────

function NewCoverModal({ onClose, onCreated }) {
  const [form, setForm] = useState({
    job_title: '',
    company: '',
    description: '',
    extra_notes: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  function set(field, value) {
    setForm(f => ({ ...f, [field]: value }))
  }

  async function handleSubmit() {
    if (!form.job_title.trim()) {
      setError('El nombre del puesto es obligatorio.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const result = await api.generateCover(form)
      if (result.error) throw new Error(result.error)
      onCreated(result)
      onClose()
    } catch (e) {
      setError(e.message || 'Error al generar la cover letter.')
    } finally {
      setLoading(false)
    }
  }

  // Cerrar con Escape
  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal">
        <div className="modal-header">
          <h2 className="modal-title">Nueva Cover Letter</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="form-field">
            <label className="form-label">Puesto <span className="form-required">*</span></label>
            <input
              className="form-input"
              placeholder="Ej: Data Engineer, Frontend Developer…"
              value={form.job_title}
              onChange={e => set('job_title', e.target.value)}
              autoFocus
            />
          </div>

          <div className="form-field">
            <label className="form-label">Empresa</label>
            <input
              className="form-input"
              placeholder="Ej: Google, Stripe…"
              value={form.company}
              onChange={e => set('company', e.target.value)}
            />
          </div>

          <div className="form-field">
            <label className="form-label">Descripción del puesto</label>
            <textarea
              className="form-textarea"
              placeholder="Pega aquí la descripción de la oferta o los requisitos…"
              rows={6}
              value={form.description}
              onChange={e => set('description', e.target.value)}
            />
          </div>

          <div className="form-field">
            <label className="form-label">Notas adicionales</label>
            <textarea
              className="form-textarea form-textarea--sm"
              placeholder="Algo que quieras destacar o que la IA tenga en cuenta…"
              rows={3}
              value={form.extra_notes}
              onChange={e => set('extra_notes', e.target.value)}
            />
          </div>

          {error && <p className="form-error">{error}</p>}
        </div>

        <div className="modal-footer">
          <button className="btn-cancel" onClick={onClose} disabled={loading}>
            Cancelar
          </button>
          <button
            className={`btn-primary${loading ? ' btn-primary--loading' : ''}`}
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner" /> Generando…
              </>
            ) : (
              '✨ Generar con IA'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Modal editar cover ────────────────────────────────────────────────────────

function EditModal({ cover, onClose, onSaved }) {
  const [title, setTitle] = useState(cover.title)
  const [content, setContent] = useState(cover.content)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSave() {
    if (!title.trim()) { setError('El título no puede estar vacío.'); return }
    setLoading(true)
    try {
      const result = await api.updateCover(cover.id, { title, content })
      if (result.error) throw new Error(result.error)
      onSaved(result)
      onClose()
    } catch (e) {
      setError(e.message || 'Error al guardar.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="modal modal--wide">
        <div className="modal-header">
          <h2 className="modal-title">Editar Cover Letter</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="form-field">
            <label className="form-label">Título</label>
            <input
              className="form-input"
              value={title}
              onChange={e => setTitle(e.target.value)}
            />
          </div>
          <div className="form-field">
            <label className="form-label">Contenido</label>
            <textarea
              className="form-textarea form-textarea--editor"
              value={content}
              onChange={e => setContent(e.target.value)}
            />
          </div>
          {error && <p className="form-error">{error}</p>}
        </div>

        <div className="modal-footer">
          <button className="btn-cancel" onClick={onClose} disabled={loading}>Cancelar</button>
          <button
            className={`btn-primary${loading ? ' btn-primary--loading' : ''}`}
            onClick={handleSave}
            disabled={loading}
          >
            {loading ? <><span className="spinner" /> Guardando…</> : '💾 Guardar'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Cover card ────────────────────────────────────────────────────────────────

function CoverCard({ cover, onEdit, onDelete }) {
  const [expanded, setExpanded] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  async function handleDownload() {
    setDownloading(true)
    try {
      const res = await api.downloadPdf(cover.id)
      if (!res.ok) throw new Error('No se pudo descargar')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `cover_${cover.id}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('Error al descargar el PDF.')
    } finally {
      setDownloading(false)
    }
  }

  function handleDelete() {
    if (!confirmDelete) { setConfirmDelete(true); return }
    onDelete(cover.id)
  }

  // Resetear confirmación si el ratón sale de la card
  function handleMouseLeave() { setConfirmDelete(false) }

  const preview = cover.content
    ? cover.content.slice(0, 200) + (cover.content.length > 200 ? '…' : '')
    : ''

  return (
    <div className="cover-card" onMouseLeave={handleMouseLeave}>
      <div className="cover-card-header">
        <div className="cover-card-meta">
          <span className="cover-card-title">{cover.title || 'Cover letter'}</span>
          {cover.company && (
            <span className="cover-card-company">— {cover.company}</span>
          )}
        </div>
        <div className="cover-card-actions">
          <button
            className="btn-icon"
            title="Vista previa"
            onClick={() => setExpanded(e => !e)}
          >
            {expanded ? '▲' : '▼'}
          </button>
          <button className="btn-icon" title="Editar" onClick={() => onEdit(cover)}>
            ✏️
          </button>
          <button
            className={`btn-icon${downloading ? ' btn-icon--loading' : ''}`}
            title="Descargar PDF"
            onClick={handleDownload}
            disabled={downloading}
          >
            {downloading ? <span className="spinner spinner--sm" /> : '⬇️'}
          </button>
          <button
            className={`btn-icon btn-icon--danger${confirmDelete ? ' btn-icon--confirm' : ''}`}
            title={confirmDelete ? 'Pulsa de nuevo para confirmar' : 'Eliminar'}
            onClick={handleDelete}
          >
            {confirmDelete ? '⚠️' : '🗑️'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="cover-card-preview">
          <pre className="cover-preview-text">{cover.content || '(sin contenido)'}</pre>
        </div>
      )}

      {!expanded && preview && (
        <p className="cover-card-snippet">{preview}</p>
      )}
    </div>
  )
}

// ── Vista principal ───────────────────────────────────────────────────────────

export default function Covers() {
  const [covers, setCovers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)
  const [editTarget, setEditTarget] = useState(null)

  useEffect(() => {
    api.getCovers()
      .then(setCovers)
      .finally(() => setLoading(false))
  }, [])

  function handleCreated(cover) {
    setCovers(prev => [cover, ...prev])
  }

  function handleSaved(updated) {
    setCovers(prev => prev.map(c => c.id === updated.id ? updated : c))
  }

  function handleDelete(id) {
    api.deleteCover(id).then(() => {
      setCovers(prev => prev.filter(c => c.id !== id))
    })
  }

  return (
    <div className="covers">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">Cover Letters</h1>
            <p className="page-subtitle">Generadas con IA a partir de tu perfil y la oferta.</p>
          </div>
          <button className="btn-new" onClick={() => setShowNew(true)}>
            + Nueva Cover
          </button>
        </div>
      </div>

      {loading ? (
        <p className="loading">Cargando…</p>
      ) : covers.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="covers-list">
          {covers.map(cover => (
            <CoverCard
              key={cover.id}
              cover={cover}
              onEdit={setEditTarget}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showNew && (
        <NewCoverModal
          onClose={() => setShowNew(false)}
          onCreated={handleCreated}
        />
      )}

      {editTarget && (
        <EditModal
          cover={editTarget}
          onClose={() => setEditTarget(null)}
          onSaved={handleSaved}
        />
      )}
    </div>
  )
}
