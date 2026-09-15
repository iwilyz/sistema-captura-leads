"""
message_generator.py
--------------------
Módulo central para la generación de mensajes personalizados, humanos y con anclaje
en Barcelona para nuevos leads en el CRM de Notion.

Incluye:
- Normalización y detección inteligente del interlocutor (persona individual vs. estudio/empresa).
- Generación de textos con variaciones dinámicas (Spintax/rotación) para evitar filtros anti-spam de WhatsApp.
- Adaptación por rubro (Arquitectura y Construcción vs. Diseño de Interiores y Acabados).
- Generación de enlaces oficiales wa.me/?text=... con el texto codificado.
"""

import re
import urllib.parse
from typing import Tuple, Optional


def limpiar_nombre_contacto(raw_name: str) -> Tuple[str, str, bool]:
    """
    Analiza el nombre comercial o razón social para determinar cómo dirigirse al contacto.
    Retorna: (saludo_destinatario, nombre_corto, es_persona_individual)
    """
    clean = raw_name.strip()
    
    # Caso especial: Arq. Claudia Lau
    if "claudia lau" in clean.lower():
        return "Arq. Claudia Lau", "Claudia Lau", True
    
    # Casos comunes de estudios y constructoras
    if "esco" in clean.lower():
        return "al equipo directivo de ESCO", "ESCO", False
    if "consizac" in clean.lower():
        return "al equipo directivo de CONSIZAC", "CONSIZAC", False
    if "mc constructora" in clean.lower():
        return "al equipo de MC Constructora", "MC Constructora", False
    if "vive más" in clean.lower() or "vive mas" in clean.lower():
        return "al equipo de Vive Más Arquitectos", "Vive Más Arquitectos", False
    if "g2a" in clean.lower():
        return "al equipo de G2A Arquitectos", "G2A Arquitectos", False
    if "mussa" in clean.lower() or "mussarq" in clean.lower():
        return "al equipo de Mussa Arquitectos", "Mussa Arquitectos", False
    if "alerq" in clean.lower():
        return "al equipo de AlerQ Arquitectos", "AlerQ Arquitectos", False
    if "atrio" in clean.lower():
        return "al equipo de Atrio Arquitectura", "Atrio Arquitectura", False
    if "ici peru" in clean.lower():
        return "al equipo de ICI Perú", "ICI Perú", False
    if "studio kreamos" in clean.lower() or "kreamos" in clean.lower():
        return "al equipo de Studio Kreamos", "Studio Kreamos", False
    if "art & glass" in clean.lower() or "vitrales" in clean.lower():
        return "al equipo de Art & Glass Vitrales", "Art & Glass Vitrales", False
        
    # Heurística genérica para futuros leads capturados
    match_arq = re.search(r"(?i)\barq(?:uitect[oa])?\.?\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+)?)", clean)
    if match_arq:
        return f"Arq. {match_arq.group(1).title()}", match_arq.group(1).title(), True
        
    nombre_limpio = re.sub(
        r"(?i)\s*-\s*(estudio de arquitectura|arquitectura & diseño|arquitectura & construcción|diseño de interiores|arquitectos|s\.a\.c\.|s\.r\.l\.).*", 
        "", 
        clean
    ).strip()
    return f"al equipo de {nombre_limpio}", nombre_limpio, False


def generar_mensaje(nombre_raw: str, rubro: str = "Arquitectura & Diseño", index: int = 0, ciudad: str = "Chiclayo") -> str:
    """
    Genera el primer mensaje de contacto personalizado con anclaje en Barcelona
    y rotación dinámica de frases para proteger contra bloqueos algorítmicos.
    """
    saludo, nombre_estudio, es_persona = limpiar_nombre_contacto(nombre_raw)
    
    rubro_norm = rubro.strip().lower()
    es_solo_diseno = (
        rubro_norm == "diseño de interiores" 
        or "vitrales" in nombre_raw.lower() 
        or "kreamos" in nombre_raw.lower()
    ) and "arquitectura" not in rubro_norm
    
    # 1. Aperturas rotativas
    aperturas_persona = [
        f"Hola {saludo}, buenas tardes. Te saluda José Zegarra directamente desde Barcelona.",
        f"Hola {saludo}, ¿cómo estás? Te escribe José Zegarra desde Barcelona.",
        f"Hola {saludo}, un gusto saludarte. Te saluda José Zegarra desde aquí en Barcelona."
    ]
    
    aperturas_empresa = [
        f"Hola {saludo}, buenas tardes. Les saluda José Zegarra directamente desde Barcelona.",
        f"Hola {saludo}, un cordial saludo. Les escribe José Zegarra desde aquí en Barcelona.",
        f"Hola {saludo}, ¿qué tal? Les saluda José Zegarra directamente desde Barcelona."
    ]
    
    apertura = aperturas_persona[index % len(aperturas_persona)] if es_persona else aperturas_empresa[index % len(aperturas_empresa)]
    
    # 2. Mención local personalizada por ciudad
    ciudad_clean = (ciudad or "Chiclayo").strip()
    if es_persona:
        mencion_local = f"Sigo el trabajo y los proyectos que vienes desarrollando en {ciudad_clean}, y justamente por eso quería escribirte:"
    else:
        menciones = [
            f"Sigo de cerca el trabajo y los proyectos que vienen desarrollando en {ciudad_clean} con {nombre_estudio}, y por eso quería escribirles:",
            f"Conozco los proyectos y la trayectoria que vienen consolidando en {ciudad_clean}, y por esa razón quería ponerme en contacto:",
            f"Vengo siguiendo de cerca el portafolio y las obras que impulsan en {ciudad_clean}, y justamente por ello les escribo:"
        ]
        mencion_local = menciones[index % len(menciones)]
        
    # 3. Propuesta de delegación técnica en Barcelona
    if es_solo_diseno:
        propuesta = (
            "Estamos coordinando la visita técnica de un grupo selecto de directores de diseño, acabados "
            "y arquitectura de Perú aquí en Barcelona. El objetivo es conectar de primera mano con tendencias europeas "
            "de interiorismo aplicado, nuevos materiales sostenibles y proveedores internacionales de vanguardia."
        )
    else:
        propuestas = [
            (
                "Estamos coordinando la visita técnica de un grupo selecto de directores de estudios y constructoras "
                "de Perú aquí en Barcelona. La idea es conectar de primera mano con centros de innovación urbana, "
                "nuevos materiales y modelos constructivos europeos aplicados."
            ),
            (
                "Estamos organizando la recepción en Barcelona de una delegación técnica de directivos de arquitectura "
                "y construcción peruanos, orientada a conocer proyectos de referencia, hubs de innovación urbana y tecnología constructiva europea."
            ),
            (
                "Estamos preparando una misión técnica en Barcelona con un grupo reducido de profesionales y constructores del norte de Perú, "
                "para acceder directamente a visitas de campo, sostenibilidad aplicada y arquitectura contemporánea europea."
            )
        ]
        propuesta = propuestas[index % len(propuestas)]
        
    # 4. Mención de brochure técnico adjunto
    if es_persona:
        adjunto = "Te adjunto por aquí el dossier en PDF con el programa de visitas y la agenda técnica para que lo puedas hojear cuando tengas 5 minutos."
    else:
        adjuntos = [
            "Les adjunto aquí el dossier técnico en PDF con el programa de visitas para que lo puedan hojear con el equipo cuando tengan un momento.",
            "Les comparto por aquí el brochure en PDF con la agenda de campo detallada para que lo puedan revisar con calma.",
            "Les dejo adjunto el dossier técnico con el itinerario de visitas para que puedan evaluarlo con la dirección."
        ]
        adjunto = adjuntos[index % len(adjuntos)]
        
    # 5. Autoridad (Web) y Canal de Difusión
    if es_persona:
        web_y_canal = (
            "Para que conozcas más sobre mi trayectoria y lo que desarrollamos desde acá:\n"
            "🌐 https://josezegarra.es\n\n"
            "Y si deseas seguir tendencias e innovación en arquitectura y construcción por Europa sin compromiso, abrí este canal de difusión oficial:\n"
            "📲 https://whatsapp.com/channel/0029Vb9Sald2Jl8D9S2Uzp1q"
        )
    else:
        web_y_canal = (
            "Para que conozcan más sobre mi trayectoria y lo que desarrollamos desde acá:\n"
            "🌐 https://josezegarra.es\n\n"
            "Y si desean seguir tendencias e innovación en arquitectura y construcción por Europa sin compromiso, abrí este canal de difusión oficial:\n"
            "📲 https://whatsapp.com/channel/0029Vb9Sald2Jl8D9S2Uzp1q"
        )
    
    # 6. Despedida cálida
    if es_persona:
        despedidas = [
            "Un saludo cordial desde Barcelona y cualquier duda me dices por aquí.",
            "Un saludo muy cordial desde Barcelona. Quedo atento a tus comentarios.",
            "Saludos cordiales desde Barcelona y quedo a tu disposición para cualquier detalle."
        ]
    else:
        despedidas = [
            "Un saludo cordial desde Barcelona y cualquier duda me comentan por aquí.",
            "Un saludo muy cordial desde Barcelona. Quedo atento a lo que necesiten.",
            "Saludos cordiales desde Barcelona y quedo a su disposición para cualquier consulta."
        ]
    despedida = despedidas[index % len(despedidas)]
    
    return f"{apertura}\n\n{mencion_local}\n\n{propuesta}\n\n{adjunto}\n\n{web_y_canal}\n\n{despedida}"


def obtener_link_whatsapp(phone: str, mensaje: str) -> Tuple[Optional[str], bool]:
    """
    Normaliza el número de teléfono peruano y genera el enlace oficial wa.me con texto pre-cargado.
    Retorna: (enlace_o_mensaje, es_movil_valido)
    """
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 9 and digits.startswith("9"):
        full_num = f"51{digits}"
    elif len(digits) == 11 and digits.startswith("519"):
        full_num = digits
    elif (len(digits) == 8 and digits.startswith("74")) or len(digits) == 6:
        return None, False  # Teléfono fijo de Chiclayo
    else:
        return None, False
        
    encoded_msg = urllib.parse.quote(mensaje)
    return f"https://wa.me/{full_num}?text={encoded_msg}", True
