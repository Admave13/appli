import { useState, useEffect, useCallback, useRef } from 'react'
import './Perfil.css'

// ── API helpers ──────────────────────────────────────────────────────────────

const api = {
  getPersonal: () => fetch('/api/personal').then(r => r.json()),
  savePersonal: (fields) => fetch('/api/personal', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fields }),
  }).then(r => r.json()),

  getSections: (category) =>
    fetch(`/api/sections?category=${encodeURIComponent(category)}`).then(r => r.json()),
  createSection: (data) => fetch('/api/sections', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => r.json()),
  updateSection: (id, data) => fetch(`/api/sections/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(r => r.json()),
  deleteSection: (id) => fetch(`/api/sections/${id}`, { method: 'DELETE' }).then(r => r.json()),
}

// ── Copy helper ──────────────────────────────────────────────────────────────

function useCopy() {
  const [copied, setCopied] = useState(null)
  const copy = useCallback((text, key) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(key)
      setTimeout(() => setCopied(null), 1400)
    })
  }, [])
  return { copy, copied }
}

// ── CopyBtn ──────────────────────────────────────────────────────────────────

function CopyBtn({ text, label, id }) {
  const { copy, copied } = useCopy()
  return (
    <button
      className={`btn-copy ${copied === id ? 'btn-copy--done' : ''}`}
      onClick={() => copy(text, id)}
    >
      {copied === id ? '✓ Copiado' : label}
    </button>
  )
}

// ── Section accordion wrapper ────────────────────────────────────────────────

function Accordion({ title, defaultOpen = true, children }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="accordion">
      <button className="accordion-header" onClick={() => setOpen(o => !o)}>
        <span className="accordion-title">{title}</span>
        <span className={`accordion-chevron ${open ? 'accordion-chevron--open' : ''}`}>v</span>
      </button>
      {open && <div className="accordion-body">{children}</div>}
    </div>
  )
}

// ── Información Personal ─────────────────────────────────────────────────────

function PersonalInfo() {
  const [fields, setFields] = useState([])
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getPersonal().then(data => {
      setFields(data.fields?.length > 0 ? data.fields : [
        { label: 'Nombre', value: '' },
        { label: 'Fecha de Nacimiento', value: '' },
      ])
      setLoading(false)
    })
  }, [])

  const updateField = (i, key, val) => {
    setFields(fs => fs.map((f, idx) => idx === i ? { ...f, [key]: val } : f))
    setSaved(false)
  }

  const addField = () => {
    setFields(fs => [...fs, { label: 'Nuevo campo', value: '' }])
    setSaved(false)
  }

  const removeField = (i) => {
    setFields(fs => fs.filter((_, idx) => idx !== i))
    setSaved(false)
  }

  const handleSave = async () => {
    await api.savePersonal(fields.filter(f => f.label.trim()))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  if (loading) return <div className="loading">Cargando…</div>

  return (
    <div className="personal-section">
      {fields.map((field, i) => (
        <div key={i} className="personal-field">
          <div className="personal-field-row">
            <input
              className="field-label-input"
              value={field.label}
              onChange={e => updateField(i, 'label', e.target.value)}
              placeholder="Nombre del campo"
            />
            <button
              className="btn-remove-field"
              onClick={() => removeField(i)}
              title="Eliminar campo"
            >×</button>
          </div>
          <div className="personal-field-value-row">
            <input
              className="field-value-input"
              value={field.value}
              onChange={e => updateField(i, 'value', e.target.value)}
              placeholder={`Ej: ${field.label}`}
            />
            <CopyBtn text={field.value} label="Copiar" id={`pf-${i}`} />
          </div>
        </div>
      ))}
      <div className="personal-actions">
        <button className="btn-add-field" onClick={addField}>
          + Añade un nuevo apartado
        </button>
        <button
          className={`btn-save ${saved ? 'btn-save--done' : ''}`}
          onClick={handleSave}
        >
          {saved ? '✓ Guardado' : 'Guardar'}
        </button>
      </div>
    </div>
  )
}

// ── Entry card (Estudios / Experiencia / Proyectos) ──────────────────────────

function EntryCard({ entry, onSave, onDelete, category }) {
  const [editing, setEditing] = useState(!entry.id)  // new entries start in edit mode
  const [form, setForm] = useState({
    title:       entry.title       || '',
    company:     entry.company     || '',
    date_period: entry.date_period || '',
    content:     entry.content     || '',
  })
  const textareaRef = useRef(null)

  // Auto-grow textarea al cambiar el contenido
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = el.scrollHeight + 'px'
  }, [form.content, editing])

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSave = async () => {
    const data = { ...form, category, tags: [] }
    const result = await (entry.id ? api.updateSection(entry.id, data) : api.createSection(data))
    onSave({ ...result, _tmpId: entry._tmpId })
    setEditing(false)
  }

  const handleDelete = async () => {
    if (!entry.id) { onDelete(entry._tmpId); return }
    await api.deleteSection(entry.id)
    onDelete(entry.id)
  }

  if (editing) {
    return (
      <div className="entry-card entry-card--editing">
        <input
          className="entry-input entry-input--title"
          placeholder="Título"
          value={form.title}
          onChange={e => update('title', e.target.value)}
        />
        <input
          className="entry-input entry-input--company"
          placeholder="Empresa / Institución"
          value={form.company}
          onChange={e => update('company', e.target.value)}
        />
        <input
          className="entry-input"
          placeholder="Periodo (ej: May 2022 - May 2024)"
          value={form.date_period}
          onChange={e => update('date_period', e.target.value)}
        />
        <textarea
          ref={textareaRef}
          className="entry-textarea"
          placeholder="Descripción"
          value={form.content}
          onChange={e => update('content', e.target.value)}
        />
        <div className="entry-edit-actions">
          <button className="btn-save" onClick={handleSave}>Guardar</button>
          {entry.id && (
            <button className="btn-cancel" onClick={() => setEditing(false)}>Cancelar</button>
          )}
          <button className="btn-danger" onClick={handleDelete}>Eliminar</button>
        </div>
      </div>
    )
  }

  return (
    <div className="entry-card">
      <div className="entry-card-header">
        <span className="entry-title">{entry.title}</span>
        {entry.date_period && (
          <span className="entry-date">{entry.date_period}</span>
        )}
      </div>
      {entry.company && (
        <p className="entry-company">{entry.company}</p>
      )}
      {entry.content && (
        <p className="entry-content">{entry.content}</p>
      )}
      <div className="entry-actions">
        <CopyBtn text={entry.title} label="Copiar Título" id={`t-${entry.id}`} />
        {entry.company && (
          <CopyBtn text={entry.company} label="Copiar Empresa" id={`co-${entry.id}`} />
        )}
        {entry.date_period && (
          <CopyBtn text={entry.date_period} label="Copiar Fecha" id={`d-${entry.id}`} />
        )}
        {entry.content && (
          <CopyBtn text={entry.content} label="Copiar Desc." id={`c-${entry.id}`} />
        )}
        <div style={{ flex: 1 }} />
        <button className="btn-danger-sm" onClick={handleDelete}>Eliminar</button>
        <button className="btn-edit" onClick={() => setEditing(true)}>Editar</button>
      </div>
    </div>
  )
}

// ── Generic section (Estudios / Experiencia / Proyectos) ─────────────────────

let tmpCounter = 0

function EntrySection({ title, category }) {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getSections(category).then(data => {
      setEntries(data)
      setLoading(false)
    })
  }, [category])

  const handleSave = (saved) => {
    setEntries(es => {
      const idx = es.findIndex(e => e.id === saved.id || e._tmpId === saved._tmpId)
      if (idx !== -1) {
        const copy = [...es]
        copy[idx] = saved
        return copy
      }
      return [...es.filter(e => e.id), saved]
    })
  }

  const handleDelete = (idOrTmp) => {
    setEntries(es => es.filter(e => e.id !== idOrTmp && e._tmpId !== idOrTmp))
  }

  const addNew = () => {
    tmpCounter++
    setEntries(es => [...es, {
      _tmpId: tmpCounter,
      id: null,
      title: '',
      date_period: '',
      content: '',
      category,
    }])
  }

  if (loading) return <div className="loading">Cargando…</div>

  return (
    <div className="entry-section">
      {entries.map(entry => (
        <EntryCard
          key={entry.id ?? `tmp-${entry._tmpId}`}
          entry={entry}
          category={category}
          onSave={handleSave}
          onDelete={handleDelete}
        />
      ))}
      <button className="btn-add-entry" onClick={addNew}>
        + Añadir {title.toLowerCase()}
      </button>
    </div>
  )
}

// ── Skills ───────────────────────────────────────────────────────────────────

function Skills() {
  const [skills, setSkills] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getSections('habilidades').then(data => {
      setSkills(data)
      setLoading(false)
    })
  }, [])

  const addSkill = async () => {
    const name = input.trim()
    if (!name) return
    const saved = await api.createSection({
      category: 'habilidades',
      title: name,
      content: '',
      date_period: '',
      tags: [],
    })
    setSkills(ss => [...ss, saved])
    setInput('')
  }

  const removeSkill = async (id) => {
    await api.deleteSection(id)
    setSkills(ss => ss.filter(s => s.id !== id))
  }

  const handleKey = (e) => {
    if (e.key === 'Enter') addSkill()
  }

  if (loading) return <div className="loading">Cargando…</div>

  return (
    <div className="skills-section">
      <div className="skills-input-row">
        <input
          className="field-value-input"
          placeholder="Añadir skill (ej: Python, Docker…)"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
        />
        <button className="btn-save" onClick={addSkill}>Añadir</button>
      </div>
      <div className="skills-list">
        {skills.map(s => (
          <span key={s.id} className="skill-tag">
            {s.title}
            <button className="skill-remove" onClick={() => removeSkill(s.id)}>×</button>
          </span>
        ))}
        {skills.length === 0 && (
          <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Aún no hay skills. Añade la primera arriba.
          </span>
        )}
      </div>
    </div>
  )
}

// ── Main Perfil view ─────────────────────────────────────────────────────────

export default function Perfil() {
  return (
    <div className="perfil">
      <div className="page-header">
        <h1 className="page-title">Mi Perfil</h1>
        <p className="page-subtitle">Gestiona toda tu información personal</p>
      </div>

      <div className="sections-list">
        <Accordion title="Información Personal" defaultOpen={true}>
          <PersonalInfo />
        </Accordion>

        <Accordion title="Experiencia" defaultOpen={false}>
          <EntrySection title="Experiencia" category="experiencia" />
        </Accordion>

        <Accordion title="Estudios" defaultOpen={false}>
          <EntrySection title="Estudios" category="estudios" />
        </Accordion>


        <Accordion title="Proyectos" defaultOpen={false}>
          <EntrySection title="Proyectos" category="proyectos" />
        </Accordion>

        <Accordion title="Skills" defaultOpen={false}>
          <Skills />
        </Accordion>
      </div>
    </div>
  )
}
