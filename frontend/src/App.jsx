import { useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import Perfil from './components/views/Perfil.jsx'
import Covers from './components/views/Covers.jsx'
import CVs from './components/views/CVs.jsx'
import Empresas from './components/views/Empresas.jsx'
import Placeholder from './components/views/Placeholder.jsx'
import './App.css'
import Aplicaciones from './components/views/Aplicaciones.jsx'
import Configuracion from './components/views/Configuracion.jsx'
import Inicio from './components/views/Inicio.jsx'

const PAGES = {
  inicio:        { label: 'Inicio',         icon: null },
  perfil:        { label: 'Perfil',          icon: null },
  empresas:      { label: 'Empresas',        icon: null },
  cvs:           { label: 'Mis CVs',         icon: null },
  covers:        { label: 'Cover Letters',   icon: null },
  aplicaciones:  { label: 'Aplicaciones',    icon: null },
  configuracion: { label: 'Configuración',   icon: null },
}

export default function App() {
  const [page, setPage] = useState('perfil')

  function renderPage() {
    if (page === 'perfil')  return <Perfil />
    if (page === 'covers')  return <Covers />
    if (page === 'cvs')     return <CVs />
    if (page === 'empresas')     return <Empresas />
    if (page === 'aplicaciones')     return <Aplicaciones />
    if (page === 'configuracion')     return <Configuracion />
    if (page === 'inicio')     return <Inicio />
    return <Placeholder name={PAGES[page]?.label ?? page} />
  }

  return (
    <div className="app-shell">
      <Sidebar pages={PAGES} current={page} onNavigate={setPage} />
      <main className="app-main">
        {renderPage()}
      </main>
    </div>
  )
}
