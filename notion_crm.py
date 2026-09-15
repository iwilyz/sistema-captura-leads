"""
notion_crm.py
-------------
Módulo cliente para gestionar el CRM de Leads en Notion mediante su API oficial.
No requiere librerías externas obligatorias (utiliza urllib y json de Python).
"""

import os
import sys
import json
import ssl
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional


class NotionCRM:
    """Cliente para interactuar con el CRM en Notion vía REST API v1."""

    NOTION_VERSION = "2022-06-28"
    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, token: Optional[str] = None, database_id: Optional[str] = None):
        # Cargar automáticamente .env si existe en el directorio
        self._load_dotenv()
        self.token = token or os.environ.get("NOTION_TOKEN", "").strip()
        self.database_id = self._clean_id(database_id or os.environ.get("NOTION_DATABASE_ID", "").strip())
        
        # Contexto SSL seguro pero tolerante
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    @staticmethod
    def _load_dotenv():
        """Lee el archivo .env local si existe y carga las variables en os.environ."""
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())

    @staticmethod
    def _clean_id(raw_id: str) -> str:
        """Limpia URLs de Notion para extraer el ID puro de 32 caracteres."""
        if not raw_id:
            return ""
        # Si pasan una URL tipo https://www.notion.so/workspace/CRM-Leads-1a2b3c4d...
        clean = raw_id.split("?")[0].split("/")[-1]
        clean = clean.replace("-", "")
        if len(clean) >= 32:
            clean = clean[-32:]
            # Formato UUID: 8-4-4-4-12
            return f"{clean[:8]}-{clean[8:12]}-{clean[12:16]}-{clean[16:20]}-{clean[20:]}"
        return raw_id

    def _request(self, endpoint: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Realiza una petición HTTP a la API de Notion."""
        if not self.token:
            raise ValueError("Falta el NOTION_TOKEN. Configúralo en tu entorno o en el archivo .env")

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.NOTION_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "LeadCaptureSystem/1.0"
        }

        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, context=self.ssl_context, timeout=20) as resp:
                response_text = resp.read().decode("utf-8")
                return json.loads(response_text)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                err_json = json.loads(error_body)
                msg = err_json.get("message", error_body)
            except Exception:
                msg = error_body
            raise RuntimeError(f"Error Notion API ({e.code}): {msg}")

    def test_connection(self) -> Dict[str, Any]:
        """Verifica la validez del token obteniendo el usuario bot autenticado."""
        return self._request("users/me")

    def create_crm_database(self, parent_page_id: str, title: str = "💼 CRM - Captura de Clientes") -> Dict[str, Any]:
        """
        Crea automáticamente la base de datos CRM con todas las columnas configuradas
        dentro de la página padre de Notion especificada.
        """
        clean_parent_id = self._clean_id(parent_page_id)
        payload = {
            "parent": {"type": "page_id", "page_id": clean_parent_id},
            "title": [{"type": "text", "text": {"content": title}}],
            "properties": {
                "Nombre": {"title": {}},
                "Estado": {
                    "select": {
                        "options": [
                            {"name": "📥 Nuevo Lead", "color": "blue"},
                            {"name": "📞 Contactado", "color": "yellow"},
                            {"name": "💬 En Conversación", "color": "orange"},
                            {"name": "📑 Propuesta Enviada", "color": "purple"},
                            {"name": "🎉 Ganado / Cliente", "color": "green"},
                            {"name": "❌ Descartado", "color": "gray"}
                        ]
                    }
                },
                "Teléfono": {"phone_number": {}},
                "WhatsApp": {"url": {}},
                "Email": {"email": {}},
                "Sitio Web": {"url": {}},
                "Ciudad": {"select": {"options": [{"name": "Chiclayo", "color": "default"}]}},
                "Rubro": {"select": {"options": [{"name": "Arquitectura & Diseño", "color": "brown"}]}},
                "Dirección": {"rich_text": {}},
                "Notas": {"rich_text": {}},
                "Mensaje Preparado": {"rich_text": {}}
            }
        }
        res = self._request("databases", method="POST", data=payload)
        self.database_id = res["id"]
        return res

    def add_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta un nuevo lead en la base de datos de Notion.
        Campos esperados en el diccionario lead:
        - name (str): Nombre del negocio / estudio
        - phone (str): Número de teléfono
        - whatsapp (str, opcional): Enlace directo de WhatsApp
        - email (str): Correo electrónico
        - website (str): Página web o red social
        - city (str): Ciudad (ej: Chiclayo)
        - address (str): Dirección física
        - category (str): Rubro (ej: Arquitectura & Diseño)
        - status (str): Estado del lead (por defecto: '📥 Nuevo Lead')
        - notes (str): Notas iniciales o fuentes
        """
        if not self.database_id:
            raise ValueError("No se ha definido database_id en el cliente NotionCRM.")

        status_val = lead.get("status", "📥 Nuevo Lead")
        # Generar enlace whatsapp si no viene dado y hay teléfono
        whatsapp_url = lead.get("whatsapp")
        if not whatsapp_url and lead.get("phone"):
            digits = "".join(filter(str.isdigit, lead["phone"]))
            if len(digits) == 9 and digits.startswith("9"):
                digits = f"51{digits}"
            if len(digits) == 11 and digits.startswith("519"):
                whatsapp_url = f"https://wa.me/{digits}"
            else:
                whatsapp_url = None

        properties = {
            "Nombre": {
                "title": [{"text": {"content": lead.get("name", "Sin Nombre")}}]
            },
            "Estado": {
                "select": {"name": status_val}
            }
        }

        if lead.get("phone"):
            properties["Teléfono"] = {"phone_number": str(lead["phone"])}

        if whatsapp_url:
            properties["WhatsApp"] = {"url": whatsapp_url}

        if lead.get("email"):
            properties["Email"] = {"email": lead["email"]}

        if lead.get("website"):
            web = lead["website"]
            if not web.startswith("http"):
                web = f"https://{web}"
            properties["Sitio Web"] = {"url": web}

        if lead.get("city"):
            properties["Ciudad"] = {"select": {"name": lead["city"]}}

        if lead.get("category"):
            properties["Rubro"] = {"select": {"name": lead["category"]}}

        if lead.get("address"):
            properties["Dirección"] = {
                "rich_text": [{"text": {"content": lead["address"]}}]
            }

        if lead.get("notes"):
            properties["Notas"] = {
                "rich_text": [{"text": {"content": lead["notes"]}}]
            }

        if lead.get("prepared_message"):
            properties["Mensaje Preparado"] = {
                "rich_text": [{"text": {"content": lead["prepared_message"]}}]
            }

        payload = {
            "parent": {"database_id": self.database_id},
            "properties": properties
        }

        return self._request("pages", method="POST", data=payload)

    def list_leads(self, page_size: int = 50) -> List[Dict[str, Any]]:
        """Obtiene la lista de leads existentes en la base de datos."""
        if not self.database_id:
            raise ValueError("No se ha configurado database_id.")
        payload = {"page_size": page_size}
        res = self._request(f"databases/{self.database_id}/query", method="POST", data=payload)
        return res.get("results", [])


if __name__ == "__main__":
    crm = NotionCRM()
    print("Módulo notion_crm inicializado correctamente.")
    if crm.token:
        try:
            bot_info = crm.test_connection()
            print(f"✅ Conexión con Notion exitosa: Bot '{bot_info.get('name', 'Bot')}'")
        except Exception as e:
            print(f"⚠️ Error al probar conexión: {e}")
    else:
        print("ℹ️ Para probar la conexión, define NOTION_TOKEN en el archivo .env o en el entorno.")
