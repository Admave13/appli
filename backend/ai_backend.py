"""
backend/ai_backend.py — Backend con APIs de IA.

Soporta: Anthropic (Claude), OpenAI, Google Gemini y Groq.
Gemini y Groq tienen tier gratuito generoso.
"""

from __future__ import annotations

import json
from typing import Any

from backend.base import (
    BaseBackend,
    CertRecommendation,
    CoverLetter,
    CVDocument,
    JobOffer,
    ProfileSection,
)

# Base URLs para proveedores compatibles con OpenAI SDK
PROVIDER_BASE_URLS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "groq":   "https://api.groq.com/openai/v1",
}

DEFAULT_MODELS = {
    "anthropic": "claude-haiku-4-5-20251001",
    "openai":    "gpt-4o-mini",
    "gemini":    "gemini-2.0-flash",
    "groq":      "llama-3.1-8b-instant",
}


class AIBackend(BaseBackend):

    def __init__(self):
        import config
        self.provider = config.AI_PROVIDER
        self.model    = config.AI_MODEL or DEFAULT_MODELS.get(config.AI_PROVIDER, "")
        self.api_key  = self._get_api_key(config)

    def _get_api_key(self, config) -> str:
        mapping = {
            "anthropic": config.ANTHROPIC_API_KEY,
            "openai":    config.OPENAI_API_KEY,
            "gemini":    getattr(config, "GEMINI_API_KEY", ""),
            "groq":      getattr(config, "GROQ_API_KEY", ""),
        }
        return mapping.get(self.provider, "")

    # ── Matching ────────────────────────────────────────────────────────────

    def match_offers(self, profile_sections, offers, filters=None):
        if not offers:
            return offers

        profile_summary = self._profile_to_text(profile_sections)
        scored = []
        for offer in offers:
            prompt = (
                "Eres un experto en selección de personal. Puntúa del 0 al 1 (con 2 decimales) "
                "cuánto encaja este perfil con la oferta. Responde SOLO con el número decimal.\n\n"
                f"PERFIL:\n{profile_summary}\n\n"
                f"OFERTA:\nTítulo: {offer.title}\nEmpresa: {offer.company}\n"
                f"Descripción: {offer.description[:1500]}"
            )
            response = self._call_llm(prompt, max_tokens=10)
            try:
                offer.score = round(float(response.strip()), 4)
            except ValueError:
                offer.score = 0.0
            scored.append(offer)

        if filters:
            if min_score := filters.get("min_score"):
                scored = [o for o in scored if o.score >= min_score]
            if tags := filters.get("tags"):
                tags_set = {t.lower() for t in tags}
                scored = [o for o in scored if tags_set & {t.lower() for t in o.tags}]
            if keyword := filters.get("keyword"):
                kw = keyword.lower()
                scored = [o for o in scored if kw in o.title.lower() or kw in o.description.lower()]

        return sorted(scored, key=lambda o: o.score, reverse=True)

    # ── CV ──────────────────────────────────────────────────────────────────

    def build_cv(self, profile_sections, offer=None):
        offer_context = ""
        if offer:
            offer_context = (
                f"\nLa oferta objetivo es:\n- Puesto: {offer.title}\n"
                f"- Empresa: {offer.company}\n- Descripción: {offer.description[:1000]}\n"
                "Adapta el orden y énfasis de las secciones para maximizar el match.\n"
            )

        prompt = (
            "Eres un experto redactor de CVs profesionales. Genera un CV completo en formato Markdown "
            "a partir de los siguientes apartados del perfil. El CV debe ser claro, conciso y profesional.\n"
            f"{offer_context}\n"
            f"APARTADOS DEL PERFIL:\n{self._sections_to_structured_text(profile_sections)}\n\n"
            "Genera el CV completo en Markdown. No inventes información que no esté en los apartados."
        )
        content = self._call_llm(prompt, max_tokens=2000)
        return CVDocument(id=None, offer_id=offer.id if offer else None,
                          sections=profile_sections, content=content)

    def adapt_cv_content(
        self,
        current_content: str,
        profile_sections: list[ProfileSection],
        offer: JobOffer,
    ) -> str:
        """Adapta un CV existente a una oferta concreta."""
        prompt = (
            "Eres un experto redactor de CVs. Tienes un CV en Markdown y una oferta de empleo. "
            "Reescribe y adapta el CV para maximizar el encaje con la oferta, "
            "sin inventar información que no esté en el CV original ni en el perfil.\n\n"
            f"OFERTA:\n- Puesto: {offer.title}\n- Empresa: {offer.company}\n"
            f"- Descripción: {offer.description[:2000]}\n\n"
            f"PERFIL (referencia adicional):\n{self._sections_to_structured_text(profile_sections)}\n\n"
            f"CV ACTUAL:\n{current_content}\n\n"
            "Devuelve SOLO el CV completo adaptado en Markdown."
        )
        return self._call_llm(prompt, max_tokens=2500)

    # ── Cover letter ─────────────────────────────────────────────────────────

    def build_cover_letter(self, profile_sections, offer, extra_notes=""):
        extra = f"\nNotas adicionales: {extra_notes}" if extra_notes else ""
        personal = next(
            (s for s in profile_sections if s.category == "información personal"), None
        )
        personal_block = (
            f"\nDATOS PERSONALES DEL CANDIDATO:\n{personal.content}\n"
            if personal else ""
        )
        prompt = (
            "Eres un experto redactor de cartas de presentación (cover letters). "
            "Escribe una cover letter profesional (con toques informales) y personalizada en español para la siguiente oferta.\n\n"
            f"OFERTA:\n- Puesto: {offer.title}\n- Empresa: {offer.company}\n"
            f"- Descripción: {offer.description[:1000]}\n\n"
            f"PERFIL DEL CANDIDATO:\n{self._sections_to_structured_text(profile_sections)}"
            f"{personal_block}"
            f"{extra}\n\n"
            "FORMATO OBLIGATORIO:\n"
            "- Empieza DIRECTAMENTE con el saludo: \"Estimado/a equipo de [Empresa]:\"\n"
            "- NO incluyas cabecera con datos del remitente (nada de nombre, teléfono, email al principio)\n"
            "- NO incluyas fecha ni \"Departamento\" ni dirección del destinatario\n"
            "- 3-4 párrafos: introducción, valor aportado, motivación, cierre\n"
            "- No expliques de más, que sean párrafos cortos\n"
            "- Centrate mas en la empresa y rol y no tanto en la descripción del puesto. Si no tiene descripción, no la tengas en cuenta y céntrate solo en el perfil del candidato\n"
            "- Termina con una despedida y el nombre real del candidato\n"
            "- Tono informal pero sabiendo a quien va dirigido\n"
            "- Destacar los puntos más relevantes del perfil para ESA oferta, pero sin copiar exactamente la descripcion.\n"
            "- NO uses placeholders como [Tu nombre] o [Tu email]; si no tienes un dato, omítelo\n"
            "- Devuelve solo el texto de la carta, sin explicaciones ni comentarios"
        )
        content = self._call_llm(prompt, max_tokens=4000)
        return CoverLetter(id=None, offer_id=offer.id if offer else None, content=content)

    def adapt_cover_content(
        self,
        current_content: str,
        profile_sections: list[ProfileSection],
        offer: JobOffer,
        extra_notes: str = "",
    ) -> str:
        """Adapta una cover letter existente a una oferta."""
        extra = f"\nNotas: {extra_notes}" if extra_notes else ""
        prompt = (
            "Eres un experto en cartas de presentación. Adapta la carta siguiente "
            "para la oferta indicada, manteniendo tono profesional en español.\n\n"
            f"OFERTA:\n- Puesto: {offer.title}\n- Empresa: {offer.company}\n"
            f"- Descripción: {offer.description[:2000]}{extra}\n\n"
            f"PERFIL:\n{self._sections_to_structured_text(profile_sections)}\n\n"
            f"CARTA ACTUAL:\n{current_content}\n\n"
            "Devuelve SOLO la carta adaptada, lista para enviar."
        )
        return self._call_llm(prompt, max_tokens=2500)

    # ── Certificaciones ──────────────────────────────────────────────────────

    def recommend_certifications(self, profile_sections, offers=None):
        offers_text = ""
        if offers:
            offers_text = "\n".join(
                f"- {o.title} en {o.company}: {o.description[:300]}" for o in offers[:5]
            )
        prompt = (
            "Eres un experto en desarrollo profesional tecnológico. Analiza el perfil y recomienda "
            "entre 3 y 6 certificaciones relevantes.\n\n"
            f"PERFIL:\n{self._sections_to_structured_text(profile_sections)}\n\n"
            f"OFERTAS ACTIVAS:\n{offers_text or 'No hay ofertas activas.'}\n\n"
            "Responde SOLO con un JSON array con este formato exacto (sin texto adicional):\n"
            '[{"name":"...","provider":"...","relevance":"...","url":"...","priority":1}]'
        )
        raw = self._call_llm(prompt, max_tokens=1000)
        try:
            data = json.loads(raw)
            return [CertRecommendation(**item) for item in data]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []

    # ── Scraping ─────────────────────────────────────────────────────────────

    def extract_offers_from_url(self, url, profile_sections=None):
        from core.scraper import Scraper
        return Scraper(ai_backend=self).scrape(url, profile_sections)

    def parse_offers_from_html(self, raw_html, source_url):
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        clean_text = soup.get_text(separator="\n", strip=True)[:8000]
        prompt = (
            "Analiza el siguiente texto de una página de ofertas de empleo y devuelve "
            "un JSON array con las ofertas. Si no hay ofertas claras, devuelve [].\n\n"
            f"TEXTO (URL: {source_url}):\n{clean_text}\n\n"
            "Responde SOLO con JSON array:\n"
            '[{"title":"...","company":"...","description":"...","url":"...","tags":[]}]'
        )
        raw = self._call_llm(prompt, max_tokens=3000)
        try:
            data = json.loads(raw)
            fields = JobOffer.__dataclass_fields__
            return [
                JobOffer(id=None, source_url=source_url,
                         **{k: v for k, v in item.items() if k in fields})
                for item in data
            ]
        except (json.JSONDecodeError, TypeError):
            return []

    # ── LLM dispatcher ───────────────────────────────────────────────────────

    def _call_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        if self.provider == "anthropic":
            return self._call_anthropic(prompt, max_tokens)
        elif self.provider in ("openai", "gemini", "groq"):
            return self._call_openai_compatible(prompt, max_tokens)
        raise ValueError(f"Proveedor desconocido: {self.provider}")

    def _call_anthropic(self, prompt: str, max_tokens: int) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        msg = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    def _call_openai_compatible(self, prompt: str, max_tokens: int) -> str:
        """Llama a cualquier API compatible con OpenAI (OpenAI, Gemini, Groq)."""
        from openai import OpenAI
        kwargs = {"api_key": self.api_key}
        if self.provider in PROVIDER_BASE_URLS:
            kwargs["base_url"] = PROVIDER_BASE_URLS[self.provider]
        client = OpenAI(**kwargs)
        resp = client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or ""

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _profile_to_text(self, sections):
        return "\n".join(f"[{s.category}] {s.title}: {s.content}" for s in sections)

    def _sections_to_structured_text(self, sections):
        parts = []
        for s in sections:
            tags = f" | Tags: {', '.join(s.tags)}" if s.tags else ""
            parts.append(f"### {s.category.upper()}: {s.title}{tags}\n{s.content}")
        return "\n\n".join(parts)
