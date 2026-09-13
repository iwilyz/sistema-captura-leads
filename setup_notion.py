"""
setup_notion.py
---------------
Asistente interactivo para configurar el CRM en Notion en 1 minuto.
- Valida el token de Notion.
- Puede crear la Base de Datos automáticamente dentro de una página de Notion que elijas.
- Guarda las credenciales en .env.
- Sube los primeros 5 leads de Chiclayo para que los veas en tu móvil de inmediato.
"""

import os
import sys
from notion_crm import NotionCRM
from seed_leads import CHICLAYO_LEADS


def prompt_or_env(prompt_text: str, env_var: str) -> str:
    val = os.environ.get(env_var, "").strip()
    if val:
        use_existing = input(f"¿Usar {env_var} existente ('{val[:10]}...')? [S/n]: ").strip().lower()
        if use_existing != "n":
            return val
    return input(prompt_text).strip()


def main():
    print("=" * 60)
    print("🚀 CONFIGURADOR AUTOMÁTICO DE NOTION CRM")
    print("=" * 60)
    print("Este asistente conectará tu Notion con el sistema de captura de clientes.\n")

    # 1. Obtener Token
    token = prompt_or_env("1. Pega tu NOTION_TOKEN (ej. ntn_... o secret_...): ", "NOTION_TOKEN")
    if not token:
        print("❌ Token no proporcionado. Abortando.")
        return

    crm = NotionCRM(token=token)
    print("\n⏳ Verificando credenciales...")
    try:
        bot = crm.test_connection()
        print(f"✅ ¡Conexión exitosa! Bot: '{bot.get('name', 'Integración Notion')}'\n")
    except Exception as e:
        print(f"❌ Error al autenticar con Notion: {e}")
        print("Asegúrate de haber creado la integración en https://www.notion.so/profile/integrations")
        return

    # 2. Base de Datos
    print("2. ¿Cómo deseas configurar la Base de Datos?")
    print("   [1] Crear automáticamente una nueva base de datos CRM en una página de Notion")
    print("   [2] Ya tengo el ID de una base de datos existente")
    opt = input("Elige una opción [1/2] (por defecto 1): ").strip() or "1"

    db_id = ""
    if opt == "1":
        page_id = input("\nPega el enlace o el ID de la página de Notion padre (donde se creará el CRM): ").strip()
        print("⏳ Creando la estructura del CRM (columnas, estados, colores)...")
        try:
            db = crm.create_crm_database(page_id)
            db_id = db["id"]
            print(f"✅ ¡Base de datos CRM creada con éxito! ID: {db_id}")
        except Exception as e:
            print(f"❌ Error al crear la base de datos: {e}")
            print("Verifica que hayas invitado/conectado a la integración en esa página de Notion.")
            return
    else:
        db_id = input("\nPega el ID o URL de tu base de datos de Notion: ").strip()
        crm.database_id = crm._clean_id(db_id)

    # 3. Guardar en .env
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f"NOTION_TOKEN={token}\n")
        f.write(f"NOTION_DATABASE_ID={crm.database_id}\n")
    print("\n✅ Configuración guardada en el archivo '.env'")

    # 4. Preguntar si subir leads iniciales
    subir = input(f"\n¿Deseas subir los {len(CHICLAYO_LEADS)} estudios de arquitectura de Chiclayo ahora? [S/n]: ").strip().lower()
    if subir != "n":
        print("\n⏳ Subiendo leads a Notion...")
        ok = 0
        for l in CHICLAYO_LEADS:
            try:
                crm.add_lead(l)
                print(f"  [OK] {l['name']}")
                ok += 1
            except Exception as e:
                print(f"  [ERROR] {l['name']}: {e}")
        print(f"\n🎉 ¡Listo! {ok}/{len(CHICLAYO_LEADS)} leads disponibles ahora mismo en tu Notion.")
        print("Abre tu app móvil de Notion para verlos en tu tablero.")


if __name__ == "__main__":
    main()
