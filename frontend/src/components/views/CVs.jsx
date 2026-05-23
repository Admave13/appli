import { useState, useEffect, useRef } from 'react'
import './CVs.css'


// ── API helpers ───────────────────────────────────────────────────────────────

async function safeJson(r) {
  const text = await r.text()
  if (!text) return {}
  try {
    return JSON.parse(text)
  } catch {
    throw new Error(`Error del servidor (${r.status})`)
  }
}

const api = {
  getCVs: () =>
    fetch('/api/cvs').then(r => safeJson(r)),

  uploadCV: (formData) =>
    fetch('/api/cvs/upload', { method: 'POST', body: formData })
      .then(async r => {
        const data = await safeJson(r)
        if (!r.ok) throw new Error(data.detail || `Error ${r.status}`)
        return data
      }),

  deleteCV: (id) =>
    fetch(`/api/cvs/${id}`, { method: 'DELETE' })
      .then(async r => {
        const data = await safeJson(r)
        if (!r.ok) throw new Error(data.detail || `Error ${r.status}`)
        return data
      }),

  downloadPdf: (id) =>
    fetch(`/api/cvs/${id}/pdf`),
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="cvs-empty">
      <div className="cvs-empty-icon">📄</div>
      <p className="cvs-empty-text">Todavía no hay CVs.</p>
      <p className="cvs-empty-sub">Pulsa «Subir CV» para añadir el primero.</p>
    </div>
  )
}

// ── Modal subir CV ────────────────────────────────────────────────────────────

function UploadModal({ onClose, onUploaded }) {
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  function handleFile(f) {
    if (!f) return
    if (f.type !== 'application/pdf') {
      setError('Solo se admiten archivos PDF.')
      return
    }
    setError(null)
    setFile(f)
    if (!title.trim()) {
      setTitle(f.name.replace(/\.pdf$/i, ''))
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  function onDragOver(e) {
    e.preventDefault()
    setDragging(true)
  }

  function onDragLeave() {
    setDragging(false)
  }

  async function handleSubmit() {
    if (!file) { setError('Selecciona un archivo PDF.'); return }
    if (!title.trim()) { setError('El título no puede estar vacío.'); return }
    setError(null)
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', title.trim())
      const result = await api.uploadCV(formData)
      if (result.detail) throw new Error(result.detail)
      onUploaded(result)
      onClose()
    } catch (e) {
      setError(e.message || 'Error al subir el CV.')
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
      <div className="modal">
        <div className="modal-header">
          <h2 className="modal-title">Subir CV</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          {/* Drop zone */}
          <div
            className={`cv-dropzone${dragging ? ' cv-dropzone--active' : ''}${file ? ' cv-dropzone--done' : ''}`}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onClick={() => !file && inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              style={{ display: 'none' }}
              onChange={e => handleFile(e.target.files[0])}
            />
            {file ? (
              <>
                <span className="cv-dropzone-icon">✅</span>
                <p className="cv-dropzone-filename">{file.name}</p>
                <button
                  className="cv-dropzone-change"
                  onClick={e => { e.stopPropagation(); setFile(null); setTitle('') }}
                >
                  Cambiar archivo
                </button>
              </>
            ) : (
              <>
                <span className="cv-dropzone-icon">📂</span>
                <p className="cv-dropzone-label">Arrastra tu CV aquí</p>
                <p className="cv-dropzone-sub">o haz clic para seleccionarlo</p>
                <p className="cv-dropzone-hint">Solo PDF</p>
              </>
            )}
          </div>

          {/* Título */}
          <div className="form-field">
            <label className="form-label">Título <span className="form-required">*</span></label>
            <input
              className="form-input"
              placeholder="Ej: CV Senior Frontend 2025"
              value={title}
              onChange={e => setTitle(e.target.value)}
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
                <span className="spinner" /> Subiendo…
              </>
            ) : (
              '⬆️ Subir CV'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── CV card ───────────────────────────────────────────────────────────────────

function CVCard({ cv, onDelete }) {
  const [downloading, setDownloading] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  async function handleDownload() {
    setDownloading(true)
    try {
      const res = await api.downloadPdf(cv.id)
      if (!res.ok) throw new Error('No se pudo descargar')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `cv_${cv.id}.pdf`
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
    onDelete(cv.id)
  }

  function handleMouseLeave() { setConfirmDelete(false) }

  return (
    <div className="cv-card" onMouseLeave={handleMouseLeave}>
      <div className="cv-card-header">
        <div className="cv-card-meta">
          <span className="cv-card-icon">📄</span>
          <span className="cv-card-title">{cv.title || 'CV'}</span>
        </div>
        <div className="cv-card-actions">
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
    </div>
  )
}

// ── Vista principal ───────────────────────────────────────────────────────────

export default function CVs() {
  const [cvs, setCVs] = useState([])
  const [loading, setLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)

  useEffect(() => {
    api.getCVs()
      .then(setCVs)
      .finally(() => setLoading(false))
  }, [])

  function handleUploaded(cv) {
    setCVs(prev => [cv, ...prev])
  }

  function handleDelete(id) {
    api.deleteCV(id).then(() => {
      setCVs(prev => prev.filter(c => c.id !== id))
    })
  }

  return (
    <div className="cvs">
      <div className="page-header">
        <div className="page-header-row">
          <div>
            <h1 className="page-title">Mis CVs</h1>
            <p className="page-subtitle">Sube tus CVs en PDF para tenerlos siempre a mano.</p>
          </div>
          <button className="btn-new" onClick={() => setShowUpload(true)}>
            + Subir CV
          </button>
        </div>
      </div>

      {loading ? (
        <p className="loading">Cargando…</p>
      ) : cvs.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="cvs-list">
          {cvs.map(cv => (
            <CVCard
              key={cv.id}
              cv={cv}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showUpload && (
        <UploadModal
          onClose={() => setShowUpload(false)}
          onUploaded={handleUploaded}
        />
      )}
    </div>
  )
}
