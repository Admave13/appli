# appli.

Asistente de búsqueda de empleo. **React + FastAPI.**

## Estructura

```
appli/
├── api.py              ← FastAPI (backend REST)
├── start.py            ← Script de arranque único
├── config.py           ← Configuración (.env)
├── requirements.txt
├── backend/            ← Lógica de IA (Gemini, Claude, OpenAI, Groq)
├── core/               ← SQLite, scraper, exportación DOCX/PDF
├── templates/          ← Plantillas DOCX
├── data/               ← Base de datos y archivos generados
└── frontend/           ← App React (Vite + HMR)
    └── src/
        ├── App.jsx
        ├── components/
        │   ├── Sidebar.jsx
        │   └── views/
        │       └── Perfil.jsx
        └── index.css
```

## Instalación

```bash
# 1. Entorno virtual Python
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Dependencias Python
pip install -r requirements.txt

# 3. Dependencias npm (solo la primera vez — start.py lo hace automáticamente)
cd frontend && npm install && cd ..

# 4. Configura IA (opcional, solo para cover letters)
cp .env.example .env
# Edita .env con tu API key
```

## Arrancar

```bash
python start.py
```

- **Frontend** → http://localhost:3000 (hot reload al editar `.jsx` / `.css`)
- **Backend**  → http://localhost:8000 (auto-reload al editar `.py`)

## IA para cover letters

```env
AI_PROVIDER=gemini          # gemini | groq | anthropic | openai
AI_MODEL=gemini-2.0-flash
GEMINI_API_KEY=tu-key
```

Gemini y Groq tienen tier gratuito.
