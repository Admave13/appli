# appli.

Proyecto de fin de semana para gestionar todo lo que necesitas cuando estás buscando trabajo: tu perfil profesional, CVs, cover letters generadas con IA y el seguimiento de tus candidaturas, todo en un mismo sitio.

**Stack:** React + FastAPI · SQLite · Soporte para Gemini, Groq, Anthropic y OpenAI.

---

## Estructura

```
appli/
├── api.py              ← FastAPI (backend REST)
├── start.py            ← Script de arranque en desarrollo
├── config.py           ← Configuración (.env)
├── requirements.txt
├── backend/            ← Lógica de IA (Gemini, Claude, OpenAI, Groq)
├── core/               ← SQLite, scraper, exportación DOCX/PDF
├── dist/               ← Ejecutable compilado (api.exe / api)
└── frontend/           ← App React (Vite)
```

---

## Instalación desde los archivos fuente (build manual)

Si no quieres usar la release precompilada, puedes construir la app de escritorio tú mismo siguiendo estos pasos. El resultado es una app nativa de Electron con el backend Python embebido.

### Requisitos previos

- Node.js 18 o superior
- Python 3.10 o superior

---

### Paso 1 — Limpiar datos sensibles

Antes de compilar, asegúrate de que no hay datos personales en los archivos:

- Elimina `.env` (conserva solo `.env.example`)
- Elimina `data/jobsearch.db`
- Vacía las carpetas `data/cvs/`, `data/covers/` y `data/logos/`
- Elimina cualquier carpeta `__pycache__`

---

### Paso 2 — Compilar el frontend (React + Vite)

Vite compila por defecto con rutas absolutas, pero Electron necesita rutas relativas para cargar los archivos via `file://`. Abre `frontend/vite.config.js` y reemplaza su contenido con esto:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',  // Crítico para que Electron cargue los recursos correctamente
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

Luego, desde la carpeta `frontend/`:

```bash
npm install
npm run build
```

Esto genera la carpeta `frontend/dist/` con la web lista.

---

### Paso 3 — Compilar el backend (FastAPI → ejecutable)

Desde la raíz del proyecto:

```bash
# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
pip install pyinstaller python-multipart

# Compilar el ejecutable
pyinstaller --onefile --name api \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import multipart \
  api.py
```

El ejecutable `api.exe` (o `api` en Mac/Linux) quedará en la carpeta `dist/`.

---

### Paso 4 — Montar el proyecto Electron

Crea una carpeta `appli-electron/` al mismo nivel que `appli/` y dentro una subcarpeta `dist-python/`. Copia el ejecutable generado en el paso anterior ahí dentro:

```
appli-electron/
├── dist-python/
│   └── api.exe          ← (o 'api' en Mac/Linux)
├── main.js
└── package.json
```

Crea `appli-electron/package.json`:

```json
{
  "name": "appli",
  "version": "1.0.0",
  "description": "Asistente de búsqueda de empleo",
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "dist": "electron-builder"
  },
  "build": {
    "appId": "com.tuapp.appli",
    "productName": "appli",
    "asar": true,
    "directories": {
      "output": "dist"
    },
    "files": [
      "main.js",
      {
        "from": "../appli/frontend/dist",
        "to": "frontend/dist"
      }
    ],
    "extraResources": [
      {
        "from": "dist-python",
        "to": ".",
        "filter": ["api.exe", "api"]
      }
    ],
    "win": {
      "target": "nsis"
    }
  },
  "devDependencies": {
    "electron": "^29.0.0",
    "electron-builder": "^24.9.1"
  }
}
```

Crea `appli-electron/main.js`:

```js
const { app, BrowserWindow, session } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const fs = require('fs')

let backendProcess = null

function startBackend() {
  const isDev = !app.isPackaged

  const apiExePath = isDev
    ? path.join(__dirname, 'dist-python', process.platform === 'win32' ? 'api.exe' : 'api')
    : path.join(process.resourcesPath, process.platform === 'win32' ? 'api.exe' : 'api')

  const userDataPath = app.getPath('userData')
  const dataDir = path.join(userDataPath, 'data')

  ;[dataDir, path.join(dataDir, 'cvs'), path.join(dataDir, 'covers'), path.join(dataDir, 'logos')]
    .forEach(dir => { if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true }) })

  backendProcess = spawn(apiExePath, [], {
    cwd: userDataPath,
    env: { ...process.env }
  })

  backendProcess.stdout.on('data', d => console.log(`[FastAPI] ${d}`))
  backendProcess.stderr.on('data', d => console.error(`[FastAPI Error] ${d}`))
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  })

  session.defaultSession.webRequest.onBeforeRequest(
    { urls: ['file://*/*/api/*'] },
    (details, callback) => {
      const newUrl = details.url.replace(/file:\/\/.*\/api\//, 'http://localhost:8000/api/')
      callback({ redirectURL: newUrl })
    }
  )

  const isDev = !app.isPackaged
  const indexPath = isDev
    ? path.join(__dirname, '../appli/frontend/dist/index.html')
    : path.join(__dirname, 'frontend/dist/index.html')

  setTimeout(() => win.loadFile(indexPath), 2500)
}

app.whenReady().then(() => {
  startBackend()
  createWindow()
})

app.on('will-quit', () => { if (backendProcess) backendProcess.kill() })
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
```

---

### Paso 5 — Probar y empaquetar

Desde la carpeta `appli-electron/`:

```bash
# Instalar dependencias de Electron
npm install

# Probar en modo desarrollo
npm start

# Generar el instalador final
npm run dist
```

El instalador quedará en `appli-electron/dist/`.

---

## Licencia

MIT
