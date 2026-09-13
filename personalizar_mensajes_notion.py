"""
personalizar_mensajes_notion.py
-------------------------------
Script de mantenimiento y actualización por lotes para nuevos leads en Notion.
Utiliza el módulo central message_generator.py para:
1. 'Mensaje Preparado': Texto redactado con anclaje en Barcelona y tono humano.
2. 'WhatsApp': Enlace oficial wa.me/?text=... para enviar con 1 solo clic desde móvil o Mac.

Solo procesa leads con estado: '📥 Nuevo Lead'.
"""

import sys
from notion_crm import NotionCRM
import message_generator


def procesar_nuevos_leads(dry_run: bool = True):
    crm = NotionCRM()
    if not crm.token or not crm.database_id:
        print("❌ Error: NOTION_TOKEN o NOTION_DATABASE_ID no configurados.")
        return

    print(f"🔄 Consultando CRM en Notion (Database ID: {crm.database_id})...")
    leads = crm.list_leads(page_size=100)
    
    # Filtrar estrictamente solo los que están en '📥 Nuevo Lead'
    nuevos = [
        l for l in leads 
        if l.get("properties", {}).get("Estado", {}).get("select", {}).get("name") == "📥 Nuevo Lead"
    ]
    
    print(f"📊 Total leads en CRM: {len(leads)} | Nuevos leads a procesar: {len(nuevos)}\n")
    if not nuevos:
        print("✅ No hay leads con estado '📥 Nuevo Lead' pendientes de procesar.")
        return
        
    actualizados = 0
    for idx, lead in enumerate(nuevos):
        page_id = lead["id"]
        props = lead.get("properties", {})
        nombre = props.get("Nombre", {}).get("title", [{}])[0].get("text", {}).get("content", "Sin Nombre")
        rubro = props.get("Rubro", {}).get("select", {}).get("name", "Arquitectura & Diseño")
        phone = props.get("Teléfono", {}).get("phone_number", "")
        
        # Generar mensaje personalizado y enlace
        mensaje = message_generator.generar_mensaje(nombre, rubro, idx)
        wa_link, es_valido = message_generator.obtener_link_whatsapp(phone, mensaje)
        
        print(f"───────────────────────────────────────────────────────────────────")
        print(f"📌 Lead #{idx+1}: {nombre} [{rubro}]")
        print(f"📞 Teléfono: {phone}")
        if es_valido and wa_link:
            print(f"🔗 Enlace WhatsApp 1-Clic: {wa_link[:75]}...")
        else:
            print(f"⚠️ Teléfono Fijo o inválido para WhatsApp")
        print(f"\n📝 Vista previa del mensaje redactado:\n{mensaje}\n")
        
        if not dry_run:
            update_props = {
                "Mensaje Preparado": {
                    "rich_text": [{"text": {"content": mensaje}}]
                }
            }
            if es_valido and wa_link:
                update_props["WhatsApp"] = {"url": wa_link}
                
            crm._request(f"pages/{page_id}", method="PATCH", data={"properties": update_props})
            print(f"✅ Lead '{nombre}' actualizado con éxito en Notion.")
            actualizados += 1
            
    print(f"───────────────────────────────────────────────────────────────────")
    if dry_run:
        print("\n🔍 Modo SIMULACIÓN finalizado. Para aplicar los cambios reales en Notion ejecuta:")
        print("   python3 personalizar_mensajes_notion.py --apply\n")
    else:
        print(f"\n🎉 ¡Proceso completado! Se actualizaron {actualizados} leads en Notion CRM.")


if __name__ == "__main__":
    is_apply = "--apply" in sys.argv
    procesar_nuevos_leads(dry_run=not is_apply)
