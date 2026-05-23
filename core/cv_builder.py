"""
core/cv_builder.py — Exportación DOCX/PDF (ReportLab, sin WeasyPrint).
"""

from __future__ import annotations

import os
from datetime import datetime

from backend.base import CoverLetter, CVDocument
from core.doc_editor import docx_to_pdf, text_to_docx
import config


class CVBuilder:
    def export_content_docx(self, content: str, path: str) -> str:
        return text_to_docx(content, path)

    def export_content_pdf_from_docx(self, docx_path: str, pdf_path: str) -> str:
        return docx_to_pdf(docx_path, pdf_path)

    def export_content_pdf(self, content: str, path: str) -> str:
        """Legacy: texto → docx temporal → pdf."""
        tmp = path.replace(".pdf", "_tmp.docx")
        text_to_docx(content, tmp)
        try:
            return docx_to_pdf(tmp, path)
        finally:
            if os.path.isfile(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass

    def export_cv_docx(self, cv: CVDocument, filename: str | None = None) -> str:
        if cv.docx_path and os.path.isfile(cv.docx_path):
            return cv.docx_path
        path = self._save_path(
            filename or f"cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}", "docx", config.DIR_CVS
        )
        text_to_docx(cv.content, path)
        return path

    def export_cv_pdf(self, cv: CVDocument, filename: str | None = None) -> str:
        path = self._save_path(
            filename or f"cv_{datetime.now().strftime('%Y%m%d_%H%M%S')}", "pdf", config.DIR_CVS
        )
        if cv.docx_path and os.path.isfile(cv.docx_path):
            return docx_to_pdf(cv.docx_path, path)
        return self.export_content_pdf(cv.content, path)

    def export_cover_docx(self, cover: CoverLetter, filename: str | None = None) -> str:
        if cover.docx_path and os.path.isfile(cover.docx_path):
            return cover.docx_path
        path = self._save_path(
            filename or f"cover_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "docx",
            config.DIR_COVERS,
        )
        text_to_docx(cover.content, path)
        return path

    def export_cover_pdf(self, cover: CoverLetter, filename: str | None = None) -> str:
        path = self._save_path(
            filename or f"cover_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "pdf",
            config.DIR_COVERS,
        )
        if cover.docx_path and os.path.isfile(cover.docx_path):
            return docx_to_pdf(cover.docx_path, path)
        return self.export_content_pdf(cover.content, path)

    def _save_path(self, name: str, ext: str, directory: str) -> str:
        os.makedirs(directory, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return os.path.join(directory, f"{safe_name}.{ext}")
