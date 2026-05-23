import { useState, useEffect } from 'react'
import './Configuracion.css'

const PROVIDERS = {
  gemini: { label: "✨ Google Gemini (por defecto)", defaultModel: "gemini-2.0-flash", envKey: "GEMINI_API_KEY" },
  groq: { label: "⚡ Groq", defaultModel: "llama-3.1-8b-instant", envKey: "GROQ_API_KEY" },
  anthropic: { label: "🤖 Anthropic Claude", defaultModel: "claude-haiku-4-5-20251001", envKey: "ANTHROPIC_API_KEY" },
  openai: { label: "🔵 OpenAI", defaultModel: "gpt-4o-mini", envKey: "OPENAI_API_KEY" }
}

const FREE_LINKS = {
  gemini: "https://aistudio.google.com/apikey",
  groq: "https://console.groq.com/keys"
}

export default function Configuracion() {
  const [provider, setProvider] = useState('gemini')
  const [apiKey, setApiKey] = useState('')
  const [model, setModel] = useState('')
  
  // Estado actual del backend reflejado
  const [backendState, setBackendState] = useState({
    provider: 'gemini',
    model: '',
    dbPath: '',
    isConfigured: false
  })
  
  const [loading, setLoading] = useState(true)
  const [saveStatus, setSaveStatus] = useState(null) // 'saving', 'done', 'error', null
  const [testResult, setTestResult] = useState({ status: null, message: '' }) // 'testing', 'success', 'error'
  const [confirmClear, setConfirmClear] = useState(false)
  const [clearStatus, setClearStatus] = useState(null)

  const fetchConfig = async () => {
    try {
      const r = await fetch('/api/config')
      if (r.ok) {
        const data = await r.json()
        setBackendState({
          provider: data.provider,
          model: data.model,
          dbPath: data.dbPath,
          isConfigured: data.isConfigured
        })
        setProvider(data.provider)
        setApiKey(data.apiKey || '')
        setModel(data.model || PROVIDERS[data.provider]?.defaultModel || '')
      }
    } catch (err) {
      console.error("Error al obtener la configuración:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfig()
  }, [])

  const handleProviderChange = (newProvider) => {
    setProvider(newProvider)
    // Setea el modelo recomendado si cambias de proveedor
    setModel(PROVIDERS[newProvider]?.defaultModel || '')
  }

  const handleSave = async () => {
    setSaveStatus('saving')
    try {
      const r = await fetch('/api/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: apiKey, model })
      })
      if (r.ok) {
        setSaveStatus('done')
        await fetchConfig()
        setTimeout(() => setSaveStatus(null), 2000)
      } else {
        setSaveStatus('error')
        setTimeout(() => setSaveStatus(null), 3000)
      }
    } catch (e) {
      setSaveStatus('error')
      setTimeout(() => setSaveStatus(null), 3000)
    }
  }

  const handleTestConnection = async () => {
    setTestResult({ status: 'testing', message: 'Probando conexión con el LLM...' })
    try {
      const r = await fetch('/api/config/test', { method: 'POST' })
      const data = await r.json()
      if (r.ok) {
        setTestResult({ status: 'success', message: `✅ Conexión correcta. Respuesta: ${data.message}` })
      } else {
        setTestResult({ status: 'error', message: `❌ Error: ${data.detail || 'Fallo de conexión'}` })
      }
    } catch (e) {
      setTestResult({ status: 'error', message: `❌ Error de red: ${e.message}` })
    }
  }

  const handleClearAll = async () => {
    if (!confirmClear) {
      setConfirmClear(true)
      return
    }
    
    setClearStatus('clearing')
    try {
      const r = await fetch('/api/system/clear-data', { method: 'DELETE' })
      if (r.ok) {
        setClearStatus('done')
        setConfirmClear(false)
        await fetchConfig()
        setTimeout(() => setClearStatus(null), 4000)
      } else {
        setClearStatus('error')
      }
    } catch (e) {
      setClearStatus('error')
    }
  }

  if (loading) return <div className="loading">Cargando configuración…</div>

  const currentProviderInfo = PROVIDERS[provider] || PROVIDERS.gemini

  return (
    <div className="perfil configuracion-view">
      <div className="page-header">
        <h1 className="page-title">⚙️ Configuración · appli.</h1>
        <p className="page-subtitle">La IA solo se usa para <strong>crear y adaptar cover letters</strong>.</p>
      </div>

      <div className="config-sections-list">
        {/* Card: Ajustes Proveedor */}
        <div className="config-card">
          <h2 className="config-section-title">🔑 Proveedor de IA</h2>
          
          <div className="config-field">
            <label className="config-label">Proveedor</label>
            <select 
              className="config-select" 
              value={provider} 
              onChange={e => handleProviderChange(e.target.value)}
            >
              {Object.entries(PROVIDERS).map(([key, info]) => (
                <option key={key} value={key}>{info.label}</option>
              ))}
            </select>
          </div>

          {FREE_LINKS[provider] && (
            <div className="config-info-link">
              <a href={FREE_LINKS[provider]} target="_blank" rel="noreferrer">
                [Obtener API key gratuita]
              </a>
            </div>
          )}

          <div className="config-field">
            <label className="config-label">API Key ({currentProviderInfo.envKey})</label>
            <input
              type="password"
              className="field-value-input"
              placeholder={`Tu ${currentProviderInfo.envKey}`}
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
            />
          </div>

          <div className="config-field">
            <label className="config-label">Modelo</label>
            <input
              type="text"
              className="field-value-input"
              placeholder={currentProviderInfo.defaultModel}
              value={model}
              onChange={e => setModel(e.target.value)}
            />
            <span className="config-caption">
              Recomendado: <code>{currentProviderInfo.defaultModel}</code>
            </span>
          </div>

          <div className="personal-actions" style={{ marginTop: '16px' }}>
            <button 
              className={`btn-save ${saveStatus === 'done' ? 'btn-save--done' : ''}`}
              onClick={handleSave}
              disabled={saveStatus === 'saving'}
            >
              {saveStatus === 'saving' ? 'Guardando...' : saveStatus === 'done' ? '✓ Guardado' : saveStatus === 'error' ? '❌ Error' : '💾 Guardar y aplicar'}
            </button>
          </div>
        </div>

        {/* Card: Info y Test de Estado */}
        <div className="config-card">
          <h2 className="config-section-title">ℹ️ Estado del Sistema</h2>
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">Proveedor activo:</span>
              <code className="status-code">{backendState.provider}</code>
            </div>
            <div className="status-item">
              <span className="status-label">Modelo activo:</span>
              <code className="status-code">{backendState.model || 'no configurado'}</code>
            </div>
            <div className="status-item">
              <span className="status-label">Estado API Key:</span>
              <code className="status-code">{backendState.isConfigured ? 'configurada' : 'pendiente'}</code>
            </div>
            <div className="status-item">
              <span className="status-label">Ruta Base de Datos:</span>
              <code className="status-code">{backendState.dbPath}</code>
            </div>
          </div>

          <div className="personal-actions" style={{ marginTop: '20px' }}>
            <button className="btn-edit" onClick={handleTestConnection} disabled={testResult.status === 'testing'}>
              🧪 Probar conexión con la IA
            </button>
          </div>

          {testResult.status && (
            <div className={`status-alert alert-${testResult.status}`}>
              {testResult.message}
            </div>
          )}
        </div>

        {/* Card: Zona de peligro */}
        <div className="config-card card-danger">
          <h2 className="config-section-title text-danger">⚠️ Zona de peligro</h2>
          <p className="danger-text">
            Borra <strong>todo</strong> de raíz: información de perfil, empresas registradas, aplicaciones guardadas, PDFs de CVs, cover letters y archivos internos en <code>data/</code>.
          </p>
          
          <div className="config-actions">
            <button 
              className="btn-danger" 
              onClick={handleClearAll}
              disabled={clearStatus === 'clearing'}
              style={{ padding: '9px 18px', fontWeight: '600' }}
            >
              {clearStatus === 'clearing' ? 'Eliminando todo...' : confirmClear ? '⚠️ Pulsa de nuevo para CONFIRMAR EL BORRADO' : '🗑️ Borrar todo lo guardado'}
            </button>
            {confirmClear && (
              <button className="btn-cancel" onClick={() => setConfirmClear(false)}>
                Cancelar
              </button>
            )}
          </div>

          {clearStatus === 'done' && (
            <div className="status-alert alert-success" style={{ marginTop: '12px' }}>
              🗑️ El sistema ha sido reseteado. Todos los datos y archivos locales fueron eliminados.
            </div>
          )}
          {clearStatus === 'error' && (
            <div className="status-alert alert-error" style={{ marginTop: '12px' }}>
              ❌ Ocurrió un error crítico inesperado al procesar el borrado masivo.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}