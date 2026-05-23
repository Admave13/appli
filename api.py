"""
api.py — FastAPI backend para appli.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List

from core.data_manager import DataManager
from backend.base import ProfileSection, CoverLetter, JobOffer, CVDocument, JobApplication

app = FastAPI(title="appli. API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dm = DataManager()


# ── Modelos Pydantic ──────────────────────────────────────────────────────────

class SectionIn(BaseModel):
    id: Optional[int] = None
    category: str
    title: str
    content: str
    company: str = ""
    date_period: str = ""
    tags: List[str] = []


class PersonalField(BaseModel):
    label: str
    value: str


class PersonalIn(BaseModel):
    fields: List[PersonalField]


class CoverGenerateIn(BaseModel):
    job_title: str
    company: str = ""
    description: str = ""
    extra_notes: str = ""


class CoverUpdateIn(BaseModel):
    title: str
    content: str

class ApplicationIn(BaseModel):
    company_id: Optional[int] = None
    company_name: str
    company_logo: str
    position: str
    status: str
    applied_at: str
    event_date: str = ""
    notes: str = ""

# ── Helpers ───────────────────────────────────────────────────────────────────

def section_to_dict(s: ProfileSection) -> dict:
    return {
        "id":          s.id,
        "category":    s.category,
        "title":       s.title,
        "content":     s.content,
        "company":     s.company,
        "date_period": s.date_period,
        "tags":        s.tags,
    }


def cover_to_dict(c: CoverLetter) -> dict:
    return {
        "id":        c.id,
        "title":     c.title,
        "content":   c.content,
        "doc_type":  c.doc_type,
        "docx_path": c.docx_path,
        "pdf_path":  c.pdf_path,
    }

def app_to_dict(a: JobApplication) -> dict:
    return {
        "id": a.id,
        "company_id": a.company_id,
        "company_name": a.company_name,
        "company_logo": a.company_logo,
        "position": a.position,
        "status": a.status,
        "applied_at": a.applied_at,
        "event_date": a.event_date,
        "notes": a.notes
    }


# ── Sections ──────────────────────────────────────────────────────────────────

@app.get("/api/sections")
def get_sections(category: Optional[str] = None):
    sections = dm.get_sections(category if category and category != "todas" else None)
    return [section_to_dict(s) for s in sections]


@app.post("/api/sections")
def create_section(data: SectionIn):
    section = ProfileSection(
        id=None,
        category=data.category,
        title=data.title,
        content=data.content,
        company=data.company,
        date_period=data.date_period,
        tags=data.tags,
    )
    saved = dm.save_section(section)
    return section_to_dict(saved)


@app.put("/api/sections/{section_id}")
def update_section(section_id: int, data: SectionIn):
    section = ProfileSection(
        id=section_id,
        category=data.category,
        title=data.title,
        content=data.content,
        company=data.company,
        date_period=data.date_period,
        tags=data.tags,
    )
    saved = dm.save_section(section)
    return section_to_dict(saved)


@app.delete("/api/sections/{section_id}")
def delete_section(section_id: int):
    dm.delete_section(section_id)
    return {"ok": True}


# ── Personal info ─────────────────────────────────────────────────────────────

@app.get("/api/personal")
def get_personal():
    sections = dm.get_sections("información personal")
    if not sections:
        return {"fields": []}
    s = sections[0]
    fields = []
    for line in s.content.split("\n"):
        if ": " in line:
            label, _, value = line.partition(": ")
            fields.append({"label": label.strip(), "value": value.strip()})
    return {"id": s.id, "fields": fields}


@app.put("/api/personal")
def save_personal(data: PersonalIn):
    existing = dm.get_sections("información personal")
    ex = existing[0] if existing else None
    content = "\n".join(f"{f.label}: {f.value}" for f in data.fields if f.value.strip())
    name = next((f.value for f in data.fields if f.label == "Nombre"), "")
    section = ProfileSection(
        id=ex.id if ex else None,
        category="información personal",
        title=name or "Personal",
        content=content,
        date_period="",
        tags=[],
    )
    saved = dm.save_section(section)
    return section_to_dict(saved)


# ── Cover Letters ─────────────────────────────────────────────────────────────

@app.get("/api/covers")
def get_covers():
    covers = dm.get_cover_letters()
    return [cover_to_dict(c) for c in covers]


@app.post("/api/covers/generate")
def generate_cover(data: CoverGenerateIn):
    import config
    if not config.ai_configured():
        raise HTTPException(
            status_code=400,
            detail="IA no configurada. Añade una API key en Configuración.",
        )

    sections = dm.get_sections()
    if not sections:
        raise HTTPException(
            status_code=400,
            detail="No hay apartados en el perfil. Ve a Perfil y añade al menos uno.",
        )

    offer = JobOffer(
        id=None,
        title=data.job_title,
        company=data.company,
        description=data.description,
        url="",
        source_url="",
    )

    backend = config.get_backend()
    cover = backend.build_cover_letter(sections, offer, data.extra_notes)
    cover.title = f"Cover — {data.job_title}" + (f" · {data.company}" if data.company else "")

    from core.cv_builder import CVBuilder
    from core.doc_editor import new_docx_path, text_to_docx

    builder   = CVBuilder()
    docx_path = new_docx_path(config.DIR_COVERS, "cover")
    text_to_docx(cover.content, docx_path)
    pdf_path  = docx_path.replace(".docx", ".pdf")
    builder.export_content_pdf_from_docx(docx_path, pdf_path)

    cover.docx_path = docx_path
    cover.pdf_path  = pdf_path
    cover.doc_type  = "editor"

    saved = dm.save_cover_letter(cover)
    return cover_to_dict(saved)


@app.put("/api/covers/{cover_id}")
def update_cover(cover_id: int, data: CoverUpdateIn):
    cover = dm.get_cover_letter(cover_id)
    if not cover:
        raise HTTPException(status_code=404, detail="Cover letter no encontrada.")

    cover.title   = data.title
    cover.content = data.content

    from core.cv_builder import CVBuilder
    from core.doc_editor import new_docx_path, text_to_docx
    import config

    builder   = CVBuilder()
    docx_path = cover.docx_path or new_docx_path(config.DIR_COVERS, "cover", cover.id)
    text_to_docx(data.content, docx_path)
    pdf_path  = docx_path.replace(".docx", ".pdf")
    builder.export_content_pdf_from_docx(docx_path, pdf_path)

    cover.docx_path = docx_path
    cover.pdf_path  = pdf_path

    saved = dm.save_cover_letter(cover)
    return cover_to_dict(saved)


@app.delete("/api/covers/{cover_id}")
def delete_cover(cover_id: int):
    dm.delete_cover_letter(cover_id)
    return {"ok": True}


@app.get("/api/covers/{cover_id}/pdf")
def download_cover_pdf(cover_id: int):
    cover = dm.get_cover_letter(cover_id)
    if not cover:
        raise HTTPException(status_code=404, detail="Cover letter no encontrada.")
    if not cover.pdf_path or not os.path.isfile(cover.pdf_path):
        raise HTTPException(status_code=404, detail="PDF no disponible todavía.")
    return FileResponse(
        cover.pdf_path,
        media_type="application/pdf",
        filename=f"cover_{cover_id}.pdf",
    )


def cv_to_dict(c: CVDocument) -> dict:
    return {
        "id":       c.id,
        "title":    c.title,
        "pdf_path": c.pdf_path,
    }


# ── CVs ───────────────────────────────────────────────────────────────────────

@app.get("/api/cvs")
def get_cvs():
    cvs = dm.get_cvs()
    return [cv_to_dict(c) for c in cvs]


@app.post("/api/cvs/upload")
async def upload_cv(
    file: UploadFile = File(...),
    title: str = Form(...),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Solo se admiten archivos PDF.")

    import config, shutil
    os.makedirs(config.DIR_CVS, exist_ok=True)

    tmp_path = os.path.join(config.DIR_CVS, f"cv_upload_{os.getpid()}.pdf")
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    cv = CVDocument(
        id=None,
        offer_id=None,
        sections=[],
        title=title,
        content="",
        doc_type="upload",
        pdf_path=tmp_path,
    )
    saved = dm.save_cv(cv)

    final_path = os.path.join(config.DIR_CVS, f"cv_{saved.id}.pdf")
    os.rename(tmp_path, final_path)
    saved.pdf_path = final_path
    saved = dm.save_cv(saved)

    return cv_to_dict(saved)


@app.delete("/api/cvs/{cv_id}")
def delete_cv(cv_id: int):
    cv = dm.get_cv(cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV no encontrado.")
    if cv.pdf_path and os.path.isfile(cv.pdf_path):
        os.remove(cv.pdf_path)
    dm.delete_cv(cv_id)
    return {"ok": True}


@app.get("/api/cvs/{cv_id}/pdf")
def download_cv_pdf(cv_id: int):
    cv = dm.get_cv(cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV no encontrado.")
    if not cv.pdf_path or not os.path.isfile(cv.pdf_path):
        raise HTTPException(status_code=404, detail="PDF no disponible.")
    return FileResponse(
        cv.pdf_path,
        media_type="application/pdf",
        filename=f"cv_{cv_id}.pdf",
    )

#----
#----
@app.get("/api/companies")
def get_companies():
    # Necesario para el selector de empresas en el modal de Aplicaciones
    return dm.get_companies()

# NUEVO: Endpoint para actualizar una empresa (Editar)
@app.put("/api/companies/{company_id}")
def update_company(company_id: int, data: dict):
    # Aseguramos que el ID de la URL se inyecte en los datos que procesa el data_manager
    data["id"] = company_id
    saved = dm.save_company(data)
    return saved

# NUEVO: Endpoint para eliminar una empresa
@app.delete("/api/companies/{company_id}")
def delete_company(company_id: int):
    # Comprobamos primero si existe la empresa para lanzar un error 404 si es necesario
    companies = dm.get_companies()
    exists = any(c["id"] == company_id for c in companies)
    if not exists:
        raise HTTPException(status_code=404, detail="Empresa no encontrada.")
    
    dm.delete_company(company_id)
    return {"ok": True}

#__________________________________

@app.get("/api/applications")
def get_applications():
    apps = dm.get_applications()
    return [app_to_dict(a) for a in apps]

@app.get("/api/applications")
def get_applications():
    apps = dm.get_applications()
    return [app_to_dict(a) for a in apps]

@app.post("/api/applications")
def create_application(data: ApplicationIn):
    app_obj = JobApplication(
        id=None,
        company_id=data.company_id,
        company_name=data.company_name,
        company_logo=data.company_logo,
        position=data.position,
        status=data.status,
        applied_at=data.applied_at,
        event_date=data.event_date,
        notes=data.notes
    )
    saved = dm.save_application(app_obj)
    return app_to_dict(saved)

@app.put("/api/applications/{app_id}")
def update_application(app_id: int, data: ApplicationIn):
    app_obj = JobApplication(
        id=app_id,
        company_id=data.company_id,
        company_name=data.company_name,
        company_logo=data.company_logo,
        position=data.position,
        status=data.status,
        applied_at=data.applied_at,
        event_date=data.event_date,
        notes=data.notes
    )
    saved = dm.save_application(app_obj)
    return app_to_dict(saved)

@app.delete("/api/applications/{app_id}")
def delete_application(app_id: int):
    dm.delete_application(app_id)
    return {"ok": True}

#-----------------------
# ── Configuration & System Endpoints ──────────────────────────────────────────

class ConfigUpdateIn(BaseModel):
    provider: str
    api_key: str
    model: str

@app.get("/api/config")
def get_config():
    import config
    # Mapeo de proveedores a sus variables de entorno correspondientes
    keys_map = {
        "gemini": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    env_key = keys_map.get(config.AI_PROVIDER, "")
    current_key = getattr(config, env_key, "") if env_key else ""
    
    return {
        "provider": config.AI_PROVIDER,
        "model": config.AI_MODEL,
        "dbPath": config.DB_PATH,
        "isConfigured": config.ai_configured(),
        "apiKey": current_key
    }

@app.put("/api/config")
def update_config(data: ConfigUpdateIn):
    import config
    from importlib import reload
    from dotenv import load_dotenv

    PROVIDERS_KEYS = {
        "gemini":    "GEMINI_API_KEY",
        "groq":      "GROQ_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai":    "OPENAI_API_KEY",
    }

    # Reconstruimos las líneas base del .env preservando configuraciones existentes
    env_lines = [
        f"AI_PROVIDER={data.provider}",
        f"AI_MODEL={data.model}",
        f"MATCH_THRESHOLD={config.MATCH_THRESHOLD}",
        f"DB_PATH={config.DB_PATH}",
    ]
    
    # Asegurar que no perdemos las llaves de los otros proveedores que ya estaban guardadas
    for p, k in PROVIDERS_KEYS.items():
        existing = getattr(config, k, "")
        val = data.api_key if p == data.provider else existing
        if val:
            env_lines.append(f"{k}={val}")

    env_path = os.path.join(os.path.dirname(__file__), ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(env_lines) + "\n")

    # Forzar la recarga en caliente de las variables de entorno de la app
    load_dotenv(env_path, override=True)
    reload(config)
    
    return {"ok": True}

@app.post("/api/config/test")
def test_config():
    import config
    if not config.ai_configured():
        raise HTTPException(
            status_code=400,
            detail="Configura la API key del proveedor seleccionado."
        )
    try:
        backend = config.get_backend()
        resp = backend._call_llm("Responde solo con la palabra: OK", max_tokens=10)
        return {"message": resp.strip()}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión con la IA: {str(e)}"
        )

@app.delete("/api/system/clear-data")
def clear_all_data():
    import config
    import shutil
    
    # 1. Limpieza completa de tablas en la base de datos local SQLite
    try:
        dm.clear_all_data()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al limpiar la base de datos: {str(e)}"
        )
        
    # 2. Vaciado físico de las carpetas de archivos adjuntos generados
    for folder in [config.DIR_CVS, config.DIR_COVERS, config.DIR_LOGOS]:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"No se pudo eliminar {file_path}: {e}")
                    
    return {"ok": True}


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
