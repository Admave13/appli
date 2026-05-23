"""
core/scraper.py — Extractor de ofertas de empleo a partir de una URL.

Estrategia en dos pasos:
  1. requests + BeautifulSoup  (rápido, sin JS — funciona en ~60 % de webs)
  2. playwright (headless)     (lento pero completo — para webs con JS / SPA)

Tras obtener el HTML, aplica heurísticas genéricas para detectar bloques
de oferta. Si se inyecta un ai_backend (AIBackend), delega el parsing al LLM.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from backend.base import JobOffer, ProfileSection
import config


# Selectores CSS que suelen contener listas de ofertas en portales comunes
_JOB_CARD_SELECTORS = [
    "[data-testid*='job']",
    "[class*='job-card']",
    "[class*='jobCard']",
    "[class*='offer']",
    "[class*='position']",
    "[class*='vacancy']",
    "article",
    "li[class*='result']",
    "li[class*='job']",
    "div[class*='result']",
]

# Patrones de texto que suelen indicar un título de oferta
_TITLE_PATTERNS = re.compile(
    r"(developer|engineer|analyst|manager|designer|consultant|"
    r"técnico|desarrollador|analista|programador|ingeniero|"
    r"coordinador|responsable|director|especialista)",
    re.IGNORECASE,
)


class Scraper:
    """
    Extrae ofertas de empleo de cualquier URL de forma genérica.

    Args:
        ai_backend: Instancia de AIBackend para parsing inteligente (opcional).
                    Si es None se usan heurísticas locales.
    """

    def __init__(self, ai_backend=None):
        self.ai_backend = ai_backend

    # ── Punto de entrada principal ────────────────────────────────────────────

    def scrape(
        self,
        url: str,
        profile_sections: list[ProfileSection] | None = None,
    ) -> list[JobOffer]:
        """
        Descarga la página y extrae las ofertas.

        Returns:
            Lista de JobOffer encontradas (sin puntuar).
        """
        html = self._fetch_html(url)
        if not html:
            return []

        if self.ai_backend and hasattr(self.ai_backend, "parse_offers_from_html"):
            # Backend IA: parsing inteligente
            offers = self.ai_backend.parse_offers_from_html(html, url)
        else:
            # Backend local: heurísticas genéricas
            offers = self._parse_with_heuristics(html, url)

        return offers[: config.SCRAPER_MAX_JOBS]

    # ── Descarga HTML ─────────────────────────────────────────────────────────

    def _fetch_html(self, url: str) -> str:
        """Intenta requests primero; si falla, usa playwright."""
        html = self._fetch_with_requests(url)
        if html and len(html) > 2000:
            return html
        return self._fetch_with_playwright(url)

    def _fetch_with_requests(self, url: str) -> str:
        try:
            import requests
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=config.SCRAPER_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except Exception:
            return ""

    def _fetch_with_playwright(self, url: str) -> str:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=config.SCRAPER_TIMEOUT * 1000)
                page.wait_for_load_state("networkidle", timeout=config.SCRAPER_TIMEOUT * 1000)
                html = page.content()
                browser.close()
                return html
        except Exception:
            return ""

    # ── Parsing heurístico ────────────────────────────────────────────────────

    def _parse_with_heuristics(self, html: str, source_url: str) -> list[JobOffer]:
        """
        Busca bloques de oferta usando selectores CSS comunes y patrones de texto.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # Eliminar ruido
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        offers: list[JobOffer] = []

        # Probar cada selector CSS hasta encontrar resultados
        for selector in _JOB_CARD_SELECTORS:
            cards = soup.select(selector)
            if len(cards) >= 2:
                for card in cards:
                    offer = self._card_to_offer(card, source_url)
                    if offer:
                        offers.append(offer)
                if offers:
                    break  # Selector encontrado, no seguir buscando

        # Fallback: buscar por enlaces con títulos que parecen ofertas
        if not offers:
            offers = self._fallback_link_extraction(soup, source_url)

        # Deduplicar por título
        seen = set()
        unique = []
        for o in offers:
            key = o.title.lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(o)

        return unique

    def _card_to_offer(self, card, source_url: str) -> JobOffer | None:
        """Convierte un nodo BeautifulSoup en un JobOffer."""
        text = card.get_text(separator=" ", strip=True)
        if len(text) < 20:
            return None

        # Título: primer encabezado o enlace con texto largo
        title = ""
        for tag in ["h1", "h2", "h3", "h4", "a", "strong"]:
            el = card.find(tag)
            if el and len(el.get_text(strip=True)) > 5:
                title = el.get_text(strip=True)
                break

        if not title or len(title) < 5:
            return None

        # Empresa: buscar patrones comunes
        company = self._extract_company(card)

        # URL de la oferta
        link = card.find("a", href=True)
        offer_url = ""
        if link:
            href = link["href"]
            offer_url = href if href.startswith("http") else urljoin(source_url, href)

        # Tags a partir del texto
        tags = self._extract_tags(text)

        return JobOffer(
            id=None,
            title=title[:255],
            company=company[:255],
            description=text[:2000],
            url=offer_url,
            source_url=source_url,
            tags=tags,
        )

    def _extract_company(self, card) -> str:
        """Heurística para extraer el nombre de la empresa de un card."""
        # Atributos data comunes
        for attr in ["data-company", "data-employer", "data-organization"]:
            val = card.get(attr, "")
            if val:
                return val

        # Clases que suelen contener la empresa
        for cls_fragment in ["company", "employer", "organization", "empresa"]:
            el = card.find(class_=re.compile(cls_fragment, re.I))
            if el:
                return el.get_text(strip=True)[:255]

        return ""

    def _extract_tags(self, text: str) -> list[str]:
        """Extrae tecnologías y habilidades comunes del texto de la oferta."""
        KNOWN_TAGS = [
            "python", "javascript", "typescript", "java", "kotlin", "swift",
            "react", "vue", "angular", "node", "django", "fastapi", "spring",
            "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
            "machine learning", "deep learning", "nlp", "data science",
            "scrum", "agile", "devops", "ci/cd", "git", "linux",
            "remote", "remoto", "híbrido", "presencial",
            "senior", "junior", "mid", "lead", "fullstack", "backend", "frontend",
        ]
        text_lower = text.lower()
        return [tag for tag in KNOWN_TAGS if tag in text_lower]

    def _fallback_link_extraction(self, soup, source_url: str) -> list[JobOffer]:
        """Último recurso: extrae todos los enlaces que parezcan ofertas."""
        offers = []
        for a in soup.find_all("a", href=True):
            title = a.get_text(strip=True)
            if _TITLE_PATTERNS.search(title) and len(title) > 10:
                href = a["href"]
                url  = href if href.startswith("http") else urljoin(source_url, href)
                offers.append(JobOffer(
                    id=None,
                    title=title[:255],
                    company="",
                    description=title,
                    url=url,
                    source_url=source_url,
                    tags=self._extract_tags(title),
                ))
        return offers
