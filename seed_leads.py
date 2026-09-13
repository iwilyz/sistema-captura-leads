"""
seed_leads.py
-------------
Contiene los leads reales capturados de estudios de arquitectura en Chiclayo.
Permite:
1. Exportar a JSON y CSV listos para usar en Excel o Google Sheets.
2. Inyectar automáticamente los leads al CRM de Notion con un solo comando.
"""

import os
import sys
import json
import csv
from notion_crm import NotionCRM

# Lista curada y verificada de leads de arquitectura en Chiclayo
CHICLAYO_LEADS = [
    {
        "name": "ESCO S.A.C. - Estudio de Arquitectura",
        "phone": "+51 923 225 227",
        "whatsapp": "https://wa.me/51923225227",
        "email": "ESPINOZA.CORPORATION.SAC@GMAIL.COM",
        "website": "https://www.esco.com.pe",
        "city": "Chiclayo",
        "address": "Chiclayo, Lambayeque, Perú",
        "category": "Arquitectura & Diseño",
        "status": "📥 Nuevo Lead",
        "notes": "Especializados en diseño integral de edificaciones, mobiliario e interiores y estudios técnicos. Tel secundario: +51 986 919 515."
    },
    {
        "name": "Vive Más Arquitectos",
        "phone": "+51 979 649 678",
        "whatsapp": "https://wa.me/51979649678",
        "email": "vivemas380@gmail.com",
        "website": "https://www.facebook.com/profile.php?id=100057546185819",
        "city": "Chiclayo",
        "address": "Calle Los Sauces, Chiclayo, Lambayeque",
        "category": "Arquitectura & Diseño",
        "status": "📥 Nuevo Lead",
        "notes": "Estudio de arquitectura y proyectos residenciales en Chiclayo. Tel alternativo: +51 929 705 612."
    },
    {
        "name": "CONSIZAC - Arquitectura & Construcción",
        "phone": "+51 945 293 512",
        "whatsapp": "https://wa.me/51945293512",
        "email": "contacto@consizac.pe",
        "website": "https://consizac.pe",
        "city": "Chiclayo",
        "address": "Chiclayo, Lambayeque",
        "category": "Arquitectura & Diseño",
        "status": "📥 Nuevo Lead",
        "notes": "Empresa de diseño y construcción de vivienda social y residencial en Chiclayo. Email proyectos: proyectos@consizac.pe. Cel adicional: +51 995 443 597."
    },
    {
        "name": "MC Constructora & Estudio de Arquitectura",
        "phone": "+51 979 667 008",
        "whatsapp": "https://wa.me/51979667008",
        "email": "contacto@mcconstructora.com",
        "website": "https://www.mcconstructora.com",
        "city": "Chiclayo",
        "address": "Calle Elías Aguirre, Chiclayo, Lambayeque",
        "category": "Arquitectura & Diseño",
        "status": "📥 Nuevo Lead",
        "notes": "Diseño arquitectónico y construcción integral. Teléfono fijo: (074) 238635. Celular ventas: +51 978 573 666."
    },
    {
        "name": "ARQA - Claudia Lau Arquitecta",
        "phone": "+51 904 349 875",
        "whatsapp": "https://wa.me/51904349875",
        "email": "informes.arqa@gmail.com",
        "website": "https://www.claudialauarquitecta.com/",
        "city": "Chiclayo",
        "address": "Cobertura Chiclayo / Piura - Zona Norte",
        "category": "Arquitectura & Diseño",
        "status": "📥 Nuevo Lead",
        "notes": "Estudio de arquitectura, interiorismo y proyectos de vivienda con presencia en la zona norte del Perú."
    }
]


def export_to_json(filepath: str = "leads_chiclayo.json"):
    """Exporta los leads a formato JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(CHICLAYO_LEADS, f, indent=2, ensure_ascii=False)
    print(f"✅ Leads exportados exitosamente a {filepath}")


def export_to_csv(filepath: str = "leads_chiclayo.csv"):
    """Exporta los leads a formato CSV compatible con Excel y Notion."""
    fieldnames = ["name", "phone", "whatsapp", "email", "website", "city", "address", "category", "status", "notes"]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead in CHICLAYO_LEADS:
            writer.writerow(lead)
    print(f"✅ Leads exportados exitosamente a {filepath}")


def sync_to_notion(token: str = None, database_id: str = None):
    """Sincroniza los leads con la base de datos de Notion."""
    crm = NotionCRM(token=token, database_id=database_id)
    if not crm.token or not crm.database_id:
        print("❌ Error: Se requiere NOTION_TOKEN y NOTION_DATABASE_ID para sincronizar.")
        print("   Configúralos en las variables de entorno o pásalos como argumento.")
        return False

    print(f"🚀 Iniciando sincronización de {len(CHICLAYO_LEADS)} leads hacia Notion...")
    success_count = 0
    for lead in CHICLAYO_LEADS:
        try:
            res = crm.add_lead(lead)
            print(f"  [OK] Lead subido: {lead['name']}")
            success_count += 1
        except Exception as e:
            print(f"  [ERROR] Falló al subir {lead['name']}: {e}")

    print(f"\n🎉 Sincronización completada: {success_count}/{len(CHICLAYO_LEADS)} subidos a Notion.")
    return True


if __name__ == "__main__":
    # 1. Exportar siempre localmente
    export_to_json()
    export_to_csv()

    # 2. Si las variables de entorno están presentes, sincronizar
    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DATABASE_ID")
    if token and db_id:
        sync_to_notion(token, db_id)
    else:
        print("\n💡 Para sincronizar con Notion:")
        print("   python3 seed_leads.py --sync")
        print("   (Asegúrate de definir NOTION_TOKEN y NOTION_DATABASE_ID en tu archivo .env)")
