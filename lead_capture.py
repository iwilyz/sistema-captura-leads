"""
lead_capture.py
---------------
Módulo para capturar y enriquecer leads comerciales B2B.
Permite:
- Normalizar números de teléfono (celulares peruanos a +51 9XXXXXXXX y fijos).
- Generar enlaces directos a WhatsApp (wa.me/...).
- Extraer correos electrónicos de sitios web mediante web scraping.
- Enviar los resultados automáticamente a Notion CRM o guardarlos en CSV/JSON.
"""

import re
import ssl
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from notion_crm import NotionCRM


class LeadCapturePipeline:
    """Pipeline de captura, enriquecimiento y almacenamiento de leads."""

    def __init__(self, crm: Optional[NotionCRM] = None):
        self.crm = crm or NotionCRM()
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

    @staticmethod
    def normalize_phone_pe(raw_phone: str) -> Optional[str]:
        """Limpia y estandariza un número de teléfono de Perú."""
        digits = re.sub(r"\D", "", raw_phone)
        # Celular con código 51 (ej: 51987654321)
        if len(digits) == 11 and digits.startswith("519"):
            return f"+51 {digits[2:5]} {digits[5:8]} {digits[8:]}"
        # Celular sin código (ej: 987654321)
        if len(digits) == 9 and digits.startswith("9"):
            return f"+51 {digits[:3]} {digits[3:6]} {digits[6:]}"
        # Teléfono fijo Chiclayo (074XXXXXX o 74XXXXXX o 238635)
        if len(digits) == 8 and digits.startswith("74"):
            return f"(074) {digits[2:]}"
        if len(digits) == 6:
            return f"(074) {digits}"
        return raw_phone.strip() if raw_phone else None

    @staticmethod
    def build_whatsapp_link(phone: str) -> Optional[str]:
        """Crea el enlace wa.me para abrir WhatsApp con un clic."""
        digits = re.sub(r"\D", "", phone or "")
        if len(digits) == 9 and digits.startswith("9"):
            return f"https://wa.me/51{digits}"
        if len(digits) == 11 and digits.startswith("519"):
            return f"https://wa.me/{digits}"
        return None

    def extract_emails_from_url(self, url: str) -> List[str]:
        """Visita una URL e intenta extraer correos electrónicos de contacto."""
        if not url or not url.startswith("http"):
            return []

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        )
        try:
            with urllib.request.urlopen(req, context=self.ssl_context, timeout=8) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                found = set(re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html))
                # Filtrar extensiones falsas o librerías
                valid = []
                for e in found:
                    lower = e.lower()
                    if not any(ext in lower for ext in [".png", ".jpg", ".jpeg", ".webp", "sentry", "wixpress", "example", "domain"]):
                        valid.append(e)
                return valid
        except Exception:
            return []

    def process_and_save(self, leads: List[Dict[str, Any]], sync_notion: bool = True) -> List[Dict[str, Any]]:
        """Normaliza los datos de cada lead y opcionalmente los envía a Notion."""
        processed = []
        for l in leads:
            item = dict(l)
            # Normalizar teléfono
            if item.get("phone"):
                item["phone"] = self.normalize_phone_pe(item["phone"])
            # Generar WhatsApp
            if not item.get("whatsapp") and item.get("phone"):
                item["whatsapp"] = self.build_whatsapp_link(item["phone"])

            # Si no tiene correo y tiene web, buscarlo
            if not item.get("email") and item.get("website"):
                emails = self.extract_emails_from_url(item["website"])
                if emails:
                    item["email"] = emails[0]

            processed.append(item)

            if sync_notion and self.crm.token and self.crm.database_id:
                try:
                    self.crm.add_lead(item)
                    print(f"  [Notion] Lead guardado: {item.get('name')}")
                except Exception as e:
                    print(f"  [Notion Error] No se pudo guardar {item.get('name')}: {e}")

        return processed


if __name__ == "__main__":
    pipeline = LeadCapturePipeline()
    test_phone = "979649678"
    print(f"Prueba normalización teléfono '{test_phone}': {pipeline.normalize_phone_pe(test_phone)}")
    print(f"Prueba WhatsApp: {pipeline.build_whatsapp_link(test_phone)}")
