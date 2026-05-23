"""
core/data_manager.py — Capa de persistencia con SQLite + SQLAlchemy.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime,
    create_engine, select, delete, text
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

import config
from backend.base import CoverLetter, CVDocument, JobOffer, ProfileSection, JobApplication


class Base(DeclarativeBase):
    pass


class ProfileSectionORM(Base):
    __tablename__ = "profile_sections"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    category     = Column(String(100), nullable=False)
    title        = Column(String(255), nullable=False)
    content      = Column(Text, nullable=False)
    company      = Column(String(255), default="")  # ◄── CAMBIO 1: Añadida columna de la empresa
    date_period  = Column(String(255), default="")
    tags_json    = Column(Text, default="[]")
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobOfferORM(Base):
    __tablename__ = "job_offers"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    title       = Column(String(255), nullable=False)
    company     = Column(String(255), default="")
    description = Column(Text, default="")
    url         = Column(Text, default="")
    source_url  = Column(Text, default="")
    tags_json   = Column(Text, default="[]")
    score       = Column(Float, default=0.0)
    created_at  = Column(DateTime, default=datetime.utcnow)


class CVDocumentORM(Base):
    __tablename__ = "cv_documents"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    offer_id   = Column(Integer, nullable=True)
    title      = Column(String(255), default="CV")
    doc_type   = Column(String(20), default="editor")
    content    = Column(Text, nullable=False, default="")
    file_path  = Column(Text, default="")
    docx_path  = Column(Text, default="")
    pdf_path   = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CoverLetterORM(Base):
    __tablename__ = "cover_letters"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    offer_id   = Column(Integer, nullable=True)
    title      = Column(String(255), default="Cover letter")
    doc_type   = Column(String(20), default="editor")
    content    = Column(Text, nullable=False, default="")
    file_path  = Column(Text, default="")
    docx_path  = Column(Text, default="")
    pdf_path   = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompanyORM(Base):
    __tablename__ = "companies"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    name         = Column(String(255), nullable=False)
    url          = Column(Text, default="")
    logo_path    = Column(Text, default="")
    notes        = Column(Text, default="")
    last_visited = Column(Text, default="")
    created_at   = Column(DateTime, default=datetime.utcnow)


class CertORM(Base):
    __tablename__ = "certifications"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    name          = Column(String(255), nullable=False)
    provider      = Column(String(255), default="")
    date_obtained = Column(String(100), default="")
    expiry        = Column(String(100), default="")
    url           = Column(Text, default="")
    notes         = Column(Text, default="")
    created_at    = Column(DateTime, default=datetime.utcnow)

class JobApplicationORM(Base):
    __tablename__ = "applications"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    company_id   = Column(Integer, nullable=True)
    company_name = Column(String(255), default="")
    company_logo = Column(Text, default="")
    position     = Column(String(255), nullable=False)
    status       = Column(String(50), default="Enviada")
    applied_at   = Column(String(100), default="")
    event_date   = Column(String(100), default="")
    notes        = Column(Text, default="")
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


_MIGRATIONS = [
    ("profile_sections", "date_period", "TEXT DEFAULT ''"),
    ("profile_sections", "company", "TEXT DEFAULT ''"),  
    ("companies", "logo_path", "TEXT DEFAULT ''"),
    ("cv_documents", "title", "TEXT DEFAULT 'CV'"),
    ("cv_documents", "doc_type", "TEXT DEFAULT 'editor'"),
    ("cv_documents", "docx_path", "TEXT DEFAULT ''"),
    ("cv_documents", "pdf_path", "TEXT DEFAULT ''"),
    ("cv_documents", "updated_at", "DATETIME"),
    ("cover_letters", "title", "TEXT DEFAULT 'Cover letter'"),
    ("cover_letters", "doc_type", "TEXT DEFAULT 'editor'"),
    ("cover_letters", "docx_path", "TEXT DEFAULT ''"),
    ("cover_letters", "pdf_path", "TEXT DEFAULT ''"),
    ("cover_letters", "updated_at", "DATETIME"),
    ("applications", "company_id", "INTEGER"),
    ("applications", "company_name", "TEXT DEFAULT ''"),
    ("applications", "company_logo", "TEXT DEFAULT ''"),
    ("applications", "position", "TEXT DEFAULT ''"),
    ("applications", "status", "TEXT DEFAULT 'Enviada'"),
    ("applications", "applied_at", "TEXT DEFAULT ''"),
    ("applications", "created_at", "TEXT DEFAULT ''"),
    ("applications", "event_date", "TEXT DEFAULT ''"),
    ("applications", "notes", "TEXT DEFAULT ''"),
    ("applications", "updated_at", "DATETIME"),
]


class DataManager:
    def __init__(self, db_url: str = config.DB_URL):
        db_path = db_url.replace("sqlite:///", "")
        if os.path.dirname(db_path):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self._migrate_schema()
        self._Session = sessionmaker(bind=self.engine)

    def _migrate_schema(self) -> None:
        with self.engine.connect() as conn:
            for table, column, col_type in _MIGRATIONS:
                try:
                    rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
                    names = {r[1] for r in rows}
                    if column not in names:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                        conn.commit()
                except Exception:
                    pass

    def _session(self) -> Session:
        return self._Session()

    # ── Profile Sections ─────────────────────────────────────────────────────

    def save_section(self, section: ProfileSection) -> ProfileSection:
        with self._session() as s:
            if section.id:
                orm = s.get(ProfileSectionORM, section.id)
                if orm:
                    orm.category     = section.category
                    orm.title        = section.title
                    orm.content      = section.content
                    orm.company      = section.company or ""  # ◄── CAMBIO 3.1: Guardar campo al actualizar
                    orm.date_period  = section.date_period or ""
                    orm.tags_json    = json.dumps(section.tags)
                    orm.updated_at   = datetime.utcnow()
            else:
                orm = ProfileSectionORM(
                    category    = section.category,
                    title       = section.title,
                    content     = section.content,
                    company     = section.company or "",  # ◄── CAMBIO 3.2: Guardar campo al insertar
                    date_period = section.date_period or "",
                    tags_json   = json.dumps(section.tags),
                )
                s.add(orm)
            s.commit()
            s.refresh(orm)
            section.id = orm.id
        return section

    def get_sections(self, category: str | None = None) -> list[ProfileSection]:
        with self._session() as s:
            stmt = select(ProfileSectionORM)
            if category:
                stmt = stmt.where(ProfileSectionORM.category == category)
            rows = s.scalars(stmt).all()
            return [self._orm_to_section(r) for r in rows]

    def delete_section(self, section_id: int) -> None:
        with self._session() as s:
            s.execute(delete(ProfileSectionORM).where(ProfileSectionORM.id == section_id))
            s.commit()

    # ── Job Offers ───────────────────────────────────────────────────────────

    def save_offer(self, offer: JobOffer) -> JobOffer:
        with self._session() as s:
            if offer.id:
                orm = s.get(JobOfferORM, offer.id)
                if orm:
                    orm.title       = offer.title
                    orm.company     = offer.company
                    orm.description = offer.description
                    orm.url         = offer.url
                    orm.source_url  = offer.source_url
                    orm.tags_json   = json.dumps(offer.tags)
                    orm.score       = offer.score
            else:
                orm = JobOfferORM(
                    title       = offer.title,
                    company     = offer.company,
                    description = offer.description,
                    url         = offer.url,
                    source_url  = offer.source_url,
                    tags_json   = json.dumps(offer.tags),
                    score       = offer.score,
                )
                s.add(orm)
            s.commit()
            s.refresh(orm)
            offer.id = orm.id
        return offer

    def get_offers(self, min_score: float = 0.0) -> list[JobOffer]:
        with self._session() as s:
            stmt = select(JobOfferORM).where(JobOfferORM.score >= min_score)
            rows = s.scalars(stmt).all()
            return [self._orm_to_offer(r) for r in rows]

    def delete_offer(self, offer_id: int) -> None:
        with self._session() as s:
            s.execute(delete(JobOfferORM).where(JobOfferORM.id == offer_id))
            s.commit()

    def clear_offers(self) -> None:
        with self._session() as s:
            s.execute(delete(JobOfferORM))
            s.commit()

    # ── CVs ──────────────────────────────────────────────────────────────────

    def save_cv(self, cv: CVDocument) -> CVDocument:
        with self._session() as s:
            if cv.id:
                orm = s.get(CVDocumentORM, cv.id)
                if orm:
                    orm.offer_id  = cv.offer_id
                    orm.title     = cv.title or "CV"
                    orm.doc_type  = cv.doc_type or "editor"
                    orm.content   = cv.content
                    orm.file_path = cv.file_path
                    orm.docx_path = cv.docx_path
                    orm.pdf_path  = cv.pdf_path
                    orm.updated_at = datetime.utcnow()
            else:
                orm = CVDocumentORM(
                    offer_id  = cv.offer_id,
                    title     = cv.title or "CV",
                    doc_type  = cv.doc_type or "editor",
                    content   = cv.content,
                    file_path = cv.file_path,
                    docx_path = cv.docx_path,
                    pdf_path  = cv.pdf_path,
                )
                s.add(orm)
            s.commit()
            s.refresh(orm)
            cv.id = orm.id
        return cv

    def get_cv(self, cv_id: int) -> CVDocument | None:
        with self._session() as s:
            orm = s.get(CVDocumentORM, cv_id)
            return self._orm_to_cv(orm) if orm else None

    def get_cvs(self) -> list[CVDocument]:
        with self._session() as s:
            rows = s.scalars(
                select(CVDocumentORM).order_by(CVDocumentORM.updated_at.desc())
            ).all()
            return [self._orm_to_cv(r) for r in rows]

    def delete_cv(self, cv_id: int) -> None:
        cv = self.get_cv(cv_id)
        if cv:
            for path in (cv.docx_path, cv.pdf_path, cv.file_path):
                if path and os.path.isfile(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
        with self._session() as s:
            s.execute(delete(CVDocumentORM).where(CVDocumentORM.id == cv_id))
            s.commit()

    # ── Cover Letters ────────────────────────────────────────────────────────

    def save_cover_letter(self, cover: CoverLetter) -> CoverLetter:
        with self._session() as s:
            if cover.id:
                orm = s.get(CoverLetterORM, cover.id)
                if orm:
                    orm.offer_id  = cover.offer_id
                    orm.title     = cover.title or "Cover letter"
                    orm.doc_type  = cover.doc_type or "editor"
                    orm.content   = cover.content
                    orm.file_path = cover.file_path
                    orm.docx_path = cover.docx_path
                    orm.pdf_path  = cover.pdf_path
                    orm.updated_at = datetime.utcnow()
            else:
                orm = CoverLetterORM(
                    offer_id  = cover.offer_id,
                    title     = cover.title or "Cover letter",
                    doc_type  = cover.doc_type or "editor",
                    content   = cover.content,
                    file_path = cover.file_path,
                    docx_path = cover.docx_path,
                    pdf_path  = cover.pdf_path,
                )
                s.add(orm)
            s.commit()
            s.refresh(orm)
            cover.id = orm.id
        return cover

    def get_cover_letter(self, cover_id: int) -> CoverLetter | None:
        with self._session() as s:
            orm = s.get(CoverLetterORM, cover_id)
            return self._orm_to_cover(orm) if orm else None

    def get_cover_letters(self) -> list[CoverLetter]:
        with self._session() as s:
            rows = s.scalars(
                select(CoverLetterORM).order_by(CoverLetterORM.updated_at.desc())
            ).all()
            return [self._orm_to_cover(r) for r in rows]

    def delete_cover_letter(self, cover_id: int) -> None:
        cover = self.get_cover_letter(cover_id)
        if cover:
            for path in (cover.docx_path, cover.pdf_path, cover.file_path):
                if path and os.path.isfile(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
        with self._session() as s:
            s.execute(delete(CoverLetterORM).where(CoverLetterORM.id == cover_id))
            s.commit()

    # ── Companies ────────────────────────────────────────────────────────────

    def save_company(self, data: dict) -> dict:
        with self._session() as s:
            company_id = data.get("id")
            if company_id:
                orm = s.get(CompanyORM, company_id)
                if orm:
                    orm.name      = data["name"]
                    orm.url       = data.get("url", "")
                    orm.notes     = data.get("notes", "")
                    if "logo_path" in data:
                        orm.logo_path = data.get("logo_path", "")
            else:
                orm = CompanyORM(
                    name      = data["name"],
                    url       = data.get("url", ""),
                    logo_path = data.get("logo_path", ""),
                    notes     = data.get("notes", ""),
                )
                s.add(orm)
            s.commit()
            s.refresh(orm)
            return self._orm_to_company(orm)

    def get_companies(self) -> list[dict]:
        with self._session() as s:
            rows = s.scalars(select(CompanyORM).order_by(CompanyORM.created_at.desc())).all()
            return [self._orm_to_company(r) for r in rows]

    def update_company_last_visited(self, company_id: int) -> None:
        with self._session() as s:
            orm = s.get(CompanyORM, company_id)
            if orm:
                orm.last_visited = datetime.now().strftime("%d/%m/%Y %H:%M")
                s.commit()

    def delete_company(self, company_id: int) -> None:
        company = next((c for c in self.get_companies() if c["id"] == company_id), None)
        if company and company.get("logo_path") and os.path.isfile(company["logo_path"]):
            try:
                os.remove(company["logo_path"])
            except OSError:
                pass
        with self._session() as s:
            s.execute(delete(CompanyORM).where(CompanyORM.id == company_id))
            s.commit()

    # ── Certifications ───────────────────────────────────────────────────────

    def save_cert(self, data: dict) -> dict:
        with self._session() as s:
            orm = CertORM(
                name          = data["name"],
                provider      = data.get("provider", ""),
                date_obtained = data.get("date_obtained", ""),
                expiry        = data.get("expiry", ""),
                url           = data.get("url", ""),
                notes         = data.get("notes", ""),
            )
            s.add(orm)
            s.commit()
            s.refresh(orm)
            return self._orm_to_cert(orm)

    def get_certs(self) -> list[dict]:
        with self._session() as s:
            rows = s.scalars(select(CertORM).order_by(CertORM.created_at.desc())).all()
            return [self._orm_to_cert(r) for r in rows]

    def delete_cert(self, cert_id: int) -> None:
        with self._session() as s:
            s.execute(delete(CertORM).where(CertORM.id == cert_id))
            s.commit()

    #-------------
    # ── Job Applications ─────────────────────────────────────────────────────

    def save_application(self, app: JobApplication) -> JobApplication:
        with self._session() as s:
            if app.id:
                orm = s.get(JobApplicationORM, app.id)
                if orm:
                    orm.company_id   = app.company_id
                    orm.company_name = app.company_name
                    orm.company_logo = app.company_logo
                    orm.position     = app.position
                    orm.status       = app.status
                    orm.applied_at   = app.applied_at
                    orm.event_date   = app.event_date
                    orm.notes        = app.notes
                    orm.updated_at   = datetime.utcnow()
            else:
                orm = JobApplicationORM(
                    company_id   = app.company_id,
                    company_name = app.company_name,
                    company_logo = app.company_logo,
                    position     = app.position,
                    status       = app.status,
                    applied_at   = app.applied_at,
                    event_date   = app.event_date,
                    notes        = app.notes
                )
                s.add(orm)
            s.commit()
            s.refresh(orm)
            app.id = orm.id
        return app

    def get_applications(self) -> list[JobApplication]:
        with self._session() as s:
            rows = s.scalars(select(JobApplicationORM).order_by(JobApplicationORM.updated_at.desc())).all()
            return [self._orm_to_application(r) for r in rows]

    def delete_application(self, app_id: int) -> None:
        with self._session() as s:
            s.execute(delete(JobApplicationORM).where(JobApplicationORM.id == app_id))
            s.commit()

    @staticmethod
    def _orm_to_application(orm: JobApplicationORM) -> JobApplication:
        return JobApplication(
            id           = orm.id,
            company_id   = orm.company_id,
            company_name = orm.company_name,
            company_logo = getattr(orm, "company_logo", None) or "",
            position     = orm.position,
            status       = orm.status,
            applied_at   = orm.applied_at,
            event_date   = getattr(orm, "event_date", None) or "",
            notes        = getattr(orm, "notes", None) or "",
        )

    # ── Limpieza total ───────────────────────────────────────────────────────

    def clear_all_data(self) -> None:
        """Borra todos los datos guardados (BD + archivos en data/)."""
        for cv in self.get_cvs():
            self.delete_cv(cv.id)
        for cover in self.get_cover_letters():
            self.delete_cover_letter(cover.id)
        for section in self.get_sections():
            self.delete_section(section.id)
        for company in self.get_companies():
            self.delete_company(company["id"])
        for cert in self.get_certs():
            self.delete_cert(cert["id"])
        self.clear_offers()

        for directory in (config.DIR_CVS, config.DIR_COVERS, "data/logos"):
            if os.path.isdir(directory):
                shutil.rmtree(directory, ignore_errors=True)
                os.makedirs(directory, exist_ok=True)

    # ── Converters ───────────────────────────────────────────────────────────

    @staticmethod
    def _orm_to_section(orm: ProfileSectionORM) -> ProfileSection:
        return ProfileSection(
            id          = orm.id,
            category    = orm.category,
            title       = orm.title,
            content     = orm.content,
            company     = getattr(orm, "company", None) or "",  # ◄── CAMBIO 4: Recuperar campo company desde la BD
            date_period = getattr(orm, "date_period", None) or "",
            tags        = json.loads(orm.tags_json or "[]"),
        )

    @staticmethod
    def _orm_to_offer(orm: JobOfferORM) -> JobOffer:
        return JobOffer(
            id          = orm.id,
            title       = orm.title,
            company     = orm.company,
            description = orm.description,
            url         = orm.url,
            source_url  = orm.source_url,
            tags        = json.loads(orm.tags_json or "[]"),
            score       = orm.score or 0.0,
        )

    @staticmethod
    def _orm_to_cv(orm: CVDocumentORM) -> CVDocument:
        return CVDocument(
            id        = orm.id,
            offer_id  = orm.offer_id,
            sections  = [],
            content   = orm.content or "",
            file_path = orm.file_path or "",
            title     = getattr(orm, "title", None) or "CV",
            doc_type  = getattr(orm, "doc_type", None) or "editor",
            docx_path = getattr(orm, "docx_path", None) or "",
            pdf_path  = getattr(orm, "pdf_path", None) or "",
        )

    @staticmethod
    def _orm_to_cover(orm: CoverLetterORM) -> CoverLetter:
        return CoverLetter(
            id        = orm.id,
            offer_id  = orm.offer_id,
            content   = orm.content or "",
            file_path = orm.file_path or "",
            title     = getattr(orm, "title", None) or "Cover letter",
            doc_type  = getattr(orm, "doc_type", None) or "editor",
            docx_path = getattr(orm, "docx_path", None) or "",
            pdf_path  = getattr(orm, "pdf_path", None) or "",
        )

    @staticmethod
    def _orm_to_company(orm: CompanyORM) -> dict:
        return {
            "id":           orm.id,
            "name":         orm.name,
            "url":          orm.url,
            "logo_path":    getattr(orm, "logo_path", None) or "",
            "notes":        orm.notes,
            "last_visited": orm.last_visited,
        }

    @staticmethod
    def _orm_to_cert(orm: CertORM) -> dict:
        return {
            "id":            orm.id,
            "name":          orm.name,
            "provider":      orm.provider,
            "date_obtained": orm.date_obtained,
            "expiry":        orm.expiry,
            "url":           orm.url,
            "notes":         orm.notes,
        }