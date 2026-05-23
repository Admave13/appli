"""
backend/base.py — Interfaz abstracta que ambos backends deben implementar.

Regla: cualquier función nueva que toque lógica de negocio va aquí primero.
Los dos backends (local e IA) implementan exactamente los mismos métodos.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import datetime


# ─────────────────────────────────────────────
#  MODELOS DE DATOS (compartidos por ambos backends)
# ─────────────────────────────────────────────

# Modificación en backend/base.py

@dataclass
class ProfileSection:
    """Un apartado del perfil del usuario (estudios, experiencia, etc.)."""
    id:          int | None
    category:    str          # e.g. "estudios", "experiencia", "proyectos"
    title:       str
    content:     str
    company:     str = ""     # ◄── ¡AÑADE ESTA LÍNEA AQUÍ!
    date_period: str = ""     # Ej: "2020 - 2024", "Marzo 2023"
    tags:        list[str] = field(default_factory=list)


@dataclass
class JobOffer:
    """Una oferta de empleo scrapeada o añadida manualmente."""
    id:          int | None
    title:       str
    company:     str
    description: str
    url:         str
    source_url:  str       # URL de la página de donde se extrajo
    tags:        list[str] = field(default_factory=list)
    score:       float = 0.0  # Puntuación de match con el perfil


@dataclass
class CVDocument:
    """Un CV en el repositorio (editable o PDF subido)."""
    id:         int | None
    offer_id:   int | None
    sections:   list[ProfileSection]
    content:    str        # Contenido editable (markdown/texto)
    file_path:  str = ""   # Legacy
    title:      str = "CV"
    doc_type:   str = "editor"   # editor | pdf
    docx_path:  str = ""
    pdf_path:   str = ""


@dataclass
class CoverLetter:
    """Una cover letter en el repositorio."""
    id:        int | None
    offer_id:  int | None
    content:   str
    file_path: str = ""
    title:     str = "Cover letter"
    doc_type:  str = "editor"
    docx_path: str = ""
    pdf_path:  str = ""

@dataclass
class JobApplication:
    id:           int | None
    company_id:   int | None  # Relación con empresa
    position:     str
    status:       str      # Enviada, Entrevista, etc.
    applied_at:   datetime.datetime    # Fecha de envío
    event_date:   datetime.datetime | None = None  # Para entrevistas/pruebas
    notes:        str = ""

@dataclass
class CertRecommendation:
    """Una certificación recomendada."""
    name:        str
    provider:    str       # e.g. "AWS", "Google", "Coursera"
    relevance:   str       # Explicación de por qué es relevante
    url:         str = ""
    priority:    int = 1   # 1 = alta, 2 = media, 3 = baja

@dataclass
class JobApplication:
    id:           int | None
    company_id:   int | None  # Relación con empresa guardada (opcional)
    company_name: str         # Nombre (copiado de la empresa o manual)
    company_logo: str         # Logo (copiado de la empresa o manual)
    position:     str
    status:       str         # Enviada, Esperando respuesta, Entrevista, Prueba tecnica, Finalizada
    applied_at:   str         # Fecha de envío (formato YYYY-MM-DD)
    event_date:   str = ""    # Fecha/Hora para entrevistas o pruebas
    notes:        str = ""


# ─────────────────────────────────────────────
#  INTERFAZ ABSTRACTA
# ─────────────────────────────────────────────

class BaseBackend(ABC):
    """
    Contrato que deben cumplir LocalBackend y AIBackend.
    La UI solo habla con esta interfaz; nunca importa directamente
    los backends concretos.
    """

    # ── Matching ────────────────────────────────

    @abstractmethod
    def match_offers(
        self,
        profile_sections: list[ProfileSection],
        offers: list[JobOffer],
        filters: dict[str, Any] | None = None,
    ) -> list[JobOffer]:
        """
        Puntúa y ordena las ofertas según su match con el perfil.

        Args:
            profile_sections: Apartados del perfil del usuario.
            offers:           Lista de ofertas a evaluar.
            filters:          Filtros opcionales (tags, puntuación mínima…).

        Returns:
            Lista de ofertas ordenadas de mayor a menor score.
        """
        ...

    # ── CV ──────────────────────────────────────

    @abstractmethod
    def build_cv(
        self,
        profile_sections: list[ProfileSection],
        offer: JobOffer | None = None,
    ) -> CVDocument:
        """
        Genera un CV adaptado a la oferta (o genérico si offer=None).

        Args:
            profile_sections: Apartados seleccionados para incluir.
            offer:            Oferta objetivo (para personalizar el CV).

        Returns:
            CVDocument con el contenido generado.
        """
        ...

    # ── Cover letter ─────────────────────────────

    @abstractmethod
    def build_cover_letter(
        self,
        profile_sections: list[ProfileSection],
        offer: JobOffer,
        extra_notes: str = "",
    ) -> CoverLetter:
        """
        Genera una cover letter para la oferta indicada.

        Args:
            profile_sections: Apartados relevantes del perfil.
            offer:            Oferta a la que se aplica.
            extra_notes:      Notas adicionales del usuario.

        Returns:
            CoverLetter con el contenido generado.
        """
        ...

    # ── Certificaciones ──────────────────────────

    @abstractmethod
    def recommend_certifications(
        self,
        profile_sections: list[ProfileSection],
        offers: list[JobOffer] | None = None,
    ) -> list[CertRecommendation]:
        """
        Recomienda certificaciones relevantes para el perfil y/o las ofertas.

        Args:
            profile_sections: Perfil del usuario.
            offers:           Ofertas activas (para detectar gaps).

        Returns:
            Lista de recomendaciones ordenadas por prioridad.
        """
        ...

    # ── Scraping ─────────────────────────────────

    @abstractmethod
    def extract_offers_from_url(
        self,
        url: str,
        profile_sections: list[ProfileSection] | None = None,
    ) -> list[JobOffer]:
        """
        Extrae ofertas de empleo de la URL indicada.

        Args:
            url:              URL de la página con ofertas.
            profile_sections: Perfil del usuario (para filtrar si procede).

        Returns:
            Lista de ofertas extraídas (sin puntuar aún).
        """
        ...
