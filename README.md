# appli.

A weekend project to manage everything you need when looking for a job: your professional profile, CVs, AI-generated cover letters, and application tracking — all in one place.

**Stack:** React + FastAPI · SQLite · Supports Gemini, Groq, Anthropic and OpenAI.

---

## Structure

```
appli/
├── api.py              ← FastAPI (REST backend)
├── start.py            ← Dev startup script
├── config.py           ← Configuration (.env)
├── requirements.txt
├── backend/            ← AI logic (Gemini, Claude, OpenAI, Groq)
├── core/               ← SQLite, scraper, DOCX/PDF export
├── dist/               ← Compiled executable (api.exe / api)
└── frontend/           ← React app (Vite)
```

---

## Building from source

If you don't want to use the prebuilt release, you can build the desktop app yourself. The result is a native Electron app with the Python backend embedded.

### Prerequisites

- Node.js 18 or higher
- Python 3.10 or higher

---

### Step 1 — Clean sensitive data

Before building, make sure no personal data is included:

- Delete `.env` (keep only `.env.example`)
- Delete `data/jobsearch.db`
- Empty the folders `data/cvs/`, `data/covers/` and `data/logos/`
- Delete any `__pycache__` folders

---

### Step 2 — Build the frontend (React + Vite)

Vite defaults to absolute paths, but Electron needs relative paths to load files via `file://`. Open `frontend/vite.config.js` and replace its contents with:

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',  // Critical: allows Electron to load assets via file://
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

Then, from the `frontend/` folder:

```bash
npm install
npm run build
```

This generates `frontend/dist/` with the compiled web app.

---

### Step 3 — Build the backend (FastAPI → executable)

From the project root:

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller python-multipart

# Build the executable
pyinstaller --onefile --name api \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import multipart \
  api.py
```

The `api.exe` (or `api` on Mac/Linux) will be generated in the `dist/` folder.

---

### Step 4 — Set up the Electron project

Create an `appli-electron/` folder at the same level as `appli/`, with a `dist-python/` subfolder inside. Copy the executable from the previous step into it:

```
appli-electron/
├── dist-python/
│   └── api.exe          ← (or 'api' on Mac/Linux)
├── main.js
└── package.json
```

Create `appli-electron/package.json`:

```json
{
  "name": "appli",
  "version": "1.0.0",
  "description": "Job search assistant",
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

Create `appli-electron/main.js`:

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

### Step 5 — Test and package

From the `appli-electron/` folder:

```bash
# Install Electron dependencies
npm install

# Test in development mode
npm start

# Build the final installer
npm run dist
```

The distributable installer will be ready in `appli-electron/dist/`.

---

## License

MIT
