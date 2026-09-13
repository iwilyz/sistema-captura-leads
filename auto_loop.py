"""
auto_loop.py
------------
Motor autónomo de captura recurrente de leads.
Diseñado para ejecutarse periódicamente (GitHub Actions o Cron local).

Flujo de ejecución:
1. Conecta con Notion CRM y recupera los leads existentes para crear el filtro anti-duplicados.
2. Carga la matriz de búsqueda (targets.json) y determina el objetivo actual.
3. Extrae y enriquece leads frescos para la ciudad/categoría objetivo.
4. Descarta duplicados (por teléfono, correo o nombre similar).
5. Inyecta los nuevos leads en Notion como '📥 Nuevo Lead'.
6. Avanza el puntero de rotación en loop_state.json para la próxima ejecución.
"""

import os
import re
import ssl
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Set
from notion_crm import NotionCRM
from lead_capture import LeadCapturePipeline


class LeadAutoLoop:
    """Orquestador del loop de captura de leads."""

    def __init__(self, targets_file: str = "targets.json", state_file: str = "loop_state.json"):
        self.crm = NotionCRM()
        self.pipeline = LeadCapturePipeline(crm=self.crm)
        self.targets_file = targets_file
        self.state_file = state_file

        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

    def load_existing_signatures(self) -> Set[str]:
        """Extrae identificadores únicos (teléfonos, emails y nombres) existentes en Notion."""
        print("🔍 Consultando leads existentes en Notion para evitar duplicados...")
        signatures = set()
        try:
            leads = self.crm.list_leads(page_size=100)
            for page in leads:
                props = page.get("properties", {})
                # Teléfono
                phone = props.get("Teléfono", {}).get("phone_number")
                if phone:
                    clean_phone = re.sub(r"\D", "", phone)
                    if clean_phone:
                        signatures.add(clean_phone[-9:])  # Últimos 9 dígitos
                # Email
                email = props.get("Email", {}).get("email")
                if email:
                    signatures.add(email.strip().lower())
                # Nombre
                name_list = props.get("Nombre", {}).get("title", [])
                if name_list:
                    name_str = name_list[0].get("plain_text", "").strip().lower()
                    if name_str:
                        # Guardar primeras 3 palabras clave del nombre
                        clean_name = re.sub(r"[^a-z0-9 ]", "", name_str)
                        signatures.add(clean_name[:25])
            print(f"✅ Se cargaron {len(signatures)} firmas únicas de leads existentes.")
        except Exception as e:
            print(f"⚠️ Advertencia al leer leads de Notion: {e}")
        return signatures

    def get_current_target(self) -> Dict[str, Any]:
        """Obtiene el objetivo actual según el estado de rotación."""
        if not os.path.exists(self.targets_file):
            raise FileNotFoundError(f"No existe el archivo {self.targets_file}")

        with open(self.targets_file, "r", encoding="utf-8") as f:
            targets = json.load(f)

        if not targets:
            raise ValueError("El archivo targets.json está vacío.")

        # Leer índice actual
        current_idx = 0
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    current_idx = state.get("next_index", 0)
            except Exception:
                current_idx = 0

        current_idx = current_idx % len(targets)
        target = targets[current_idx]

        # Guardar siguiente índice
        next_idx = (current_idx + 1) % len(targets)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump({"next_index": next_idx, "last_target": target["id"]}, f, indent=2)

        return target

    def search_leads_online(self, target: Dict[str, Any], max_results: int = 15) -> List[Dict[str, Any]]:
        """
        Ejecuta la búsqueda de leads en internet para el objetivo especificado.
        Combina directorios empresariales y fuentes web verificadas.
        """
        city = target.get("city", "Chiclayo")
        category = target.get("category", "Arquitectura & Diseño")
        query = target.get("query", f"estudios de arquitectura {city}")

        print(f"🌐 Buscando prospectos para: '{query}' (Ciudad: {city})...")
        found_leads = []

        # Consulta a Páginas Amarillas Perú (formato Next.js)
        encoded_city = urllib.parse.quote(city.lower())
        cat_slug = "arquitectos" if "arquitect" in query.lower() else "diseno-de-interiores"
        url = f"https://www.paginasamarillas.com.pe/{encoded_city}/servicios/{cat_slug}"

        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
            with urllib.request.urlopen(req, context=self.ssl_context, timeout=12) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                match = re.search(r"<script id=\"__NEXT_DATA__\" type=\"application/json\">(.*?)</script>", html)
                if match:
                    data = json.loads(match.group(1))
                    results = data.get("props", {}).get("pageProps", {}).get("results", [])
                    for r in results[:max_results]:
                        name = r.get("name")
                        if not name:
                            continue

                        # Teléfonos
                        phones = []
                        if r.get("mainPhone") and r["mainPhone"].get("number"):
                            phones.append(r["mainPhone"]["number"])
                        for addr in r.get("allAddresses") or []:
                            for p in addr.get("allPhones") or []:
                                num = p.get("number")
                                if num and num not in phones:
                                    phones.append(num)

                        primary_phone = phones[0] if phones else None
                        
                        # Emails
                        emails = r.get("emails") or []
                        primary_email = emails[0] if emails else None

                        # Web y RRSS
                        contact_map = r.get("contactMap") or {}
                        webs = contact_map.get("WEB") or []
                        was = contact_map.get("WHATSAPP") or []
                        website = webs[0] if webs else (r.get("urlWeb") or None)
                        whatsapp_link = was[0] if was else None

                        # Dirección
                        addr_str = None
                        if r.get("mainAddress"):
                            st = r["mainAddress"].get("streetName") or ""
                            loc = r["mainAddress"].get("localityToShow") or city
                            addr_str = f"{st} ({loc})".strip()

                        lead = {
                            "name": name,
                            "phone": primary_phone,
                            "whatsapp": whatsapp_link,
                            "email": primary_email,
                            "website": website,
                            "city": city,
                            "category": category,
                            "address": addr_str,
                            "status": "📥 Nuevo Lead",
                            "notes": f"Capturado automáticamente en rutina recurrente ({query})."
                        }
                        found_leads.append(lead)
        except Exception as e:
            print(f"⚠️ Error en consulta online: {e}")

        return found_leads

    def run(self, max_new_leads: int = 10) -> int:
        """Ejecuta el ciclo completo del loop."""
        print("=" * 60)
        print("🚀 INICIANDO RUTINA DE CAPTURA AUTOMÁTICA DE LEADS")
        print("=" * 60)

        # 1. Obtener objetivo actual
        target = self.get_current_target()
        print(f"🎯 Objetivo seleccionado: {target['id']} -> '{target['query']}'")

        # 2. Cargar firmas para deduplicación
        signatures = self.load_existing_signatures()

        # 3. Buscar prospectos
        raw_leads = self.search_leads_online(target, max_results=max_new_leads + 10)
        print(f"🔎 Se encontraron {len(raw_leads)} prospectos brutos.")

        # 4. Filtrar duplicados
        new_unique_leads = []
        for lead in raw_leads:
            # Check de teléfono
            phone = lead.get("phone")
            is_dup = False
            if phone:
                clean_phone = re.sub(r"\D", "", phone)
                if clean_phone and clean_phone[-9:] in signatures:
                    is_dup = True

            # Check de email
            email = lead.get("email")
            if not is_dup and email and email.strip().lower() in signatures:
                is_dup = True

            # Check de nombre
            name = lead.get("name", "")
            clean_name = re.sub(r"[^a-z0-9 ]", "", name.lower())[:25]
            if not is_dup and clean_name and clean_name in signatures:
                is_dup = True

            if not is_dup:
                new_unique_leads.append(lead)
                # Agregar al set para no duplicar dentro del mismo lote
                if phone:
                    signatures.add(re.sub(r"\D", "", phone)[-9:])
                if email:
                    signatures.add(email.strip().lower())
                if clean_name:
                    signatures.add(clean_name)

            if len(new_unique_leads) >= max_new_leads:
                break

        print(f"✨ Leads únicos filtrados listos para insertar: {len(new_unique_leads)}")

        # 5. Enriquecer y enviar a Notion
        uploaded_count = 0
        if new_unique_leads:
            print("⏳ Enriqueciendo datos e inyectando en Notion CRM...")
            processed = self.pipeline.process_and_save(new_unique_leads, sync_notion=True)
            uploaded_count = len(processed)
        else:
            print("ℹ️ No hubo leads nuevos en esta rotación (todos ya existían en tu base de datos).")

        print("=" * 60)
        print(f"🎉 RUTINA FINALIZADA: {uploaded_count} leads nuevos sincronizados con Notion.")
        print("=" * 60)
        return uploaded_count


if __name__ == "__main__":
    max_leads_env = int(os.environ.get("MAX_LEADS", "8"))
    loop = LeadAutoLoop()
    loop.run(max_new_leads=max_leads_env)
