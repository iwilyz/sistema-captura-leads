# 🚀 Sistema de Captura de Clientes (Leads B2B) & CRM en Notion

Sistema automatizado para la **captación, enriquecimiento y gestión de leads comerciales** (arquitectos, empresas, profesionales) a partir de fuentes geográficas y web (Google Maps, directorios comerciales, sitios web), integrado con **Notion** como CRM móvil y de escritorio.

---

## 📌 Contexto del Proyecto (Para Claude / Desarrolladores)

* **Objetivo Principal:** Diseñar e implementar un motor de captura de prospectos locales/regionales, enriqueciendo su información (teléfono, WhatsApp directo, correo electrónico y web) y sincronizándolos automáticamente con un CRM visual y gratuito en Notion.
* **Caso de Prueba / Demostración Inicial:** 5 estudios de arquitectura con presencia en la ciudad de **Chiclayo, Lambayeque, Perú**.
* **Estado Actual:**
  * ✅ Extracción inicial completada y verificada para Chiclayo.
  * ✅ Base de Datos Notion creada y vinculada con éxito (**"💼 Embudo de Clientes - Chiclayo"**).
  * ✅ **5 Leads reales de Chiclayo ya sincronizados y disponibles en la cuenta de Notion del usuario**.
  * ✅ Archivos de datos generados en local: `leads_chiclayo.json` y `leads_chiclayo.csv`.
  * ✅ Módulo cliente de Notion API implementado (`notion_crm.py`) con cero dependencias externas requeridas (Python puro).
  * ✅ Credenciales guardadas de forma segura en `.env`.

---

## 📂 Estructura de Archivos

```
Sistema Captura de Clientes/
├── README.md                  # Este documento (visión general e instrucciones)
├── DOCUMENTACION_SISTEMA.md   # Arquitectura técnica detallada y diseño del pipeline
├── FUNNEL_PROSPECCION.md      # Playbook de ventas, guiones de WhatsApp y cadencia de seguimiento
├── auto_loop.py               # Motor autónomo del loop recurrente y deduplicación
├── targets.json               # Matriz de objetivos rotativos (ciudades y categorías)
├── loop_state.json            # Memoria del estado de rotación actual
├── notion_crm.py              # Cliente API oficial de Notion (creación de DB y carga de leads)
├── lead_capture.py            # Motor de enriquecimiento, normalización telefónica y extracción web
├── seed_leads.py              # Datos de los primeros estudios de Chiclayo + exportación
├── setup_notion.py            # Asistente interactivo en terminal para vincular Notion
├── leads_chiclayo.json        # Leads en formato JSON estructurado
├── leads_chiclayo.csv         # Leads en formato CSV (listo para abrir en Excel o Google Sheets)
├── .github/workflows/         # Automatización en la nube (GitHub Actions)
│   └── lead_generation_loop.yml
└── .env.example               # Plantilla de variables de entorno para credenciales
```

---

## ☁️ Rutina Automática en la Nube (GitHub Actions)

Para que el sistema capture leads frescos **todos los lunes a las 8:00 AM (Hora Perú)** sin necesidad de tener tu ordenador encendido:

1. **Crea un repositorio privado en GitHub:**
   * Entra en [github.com/new](https://github.com/new) y crea un repositorio (ej: `sistema-captura-leads`), márcalo como **Private**.
2. **Sube tu proyecto:**
   ```bash
   git init
   git add .
   git commit -m "feat: initial commit sistema captura leads"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/sistema-captura-leads.git
   git push -u origin main
   ```
3. **Agrega tus Secretos en GitHub:**
   * En tu repositorio de GitHub ve a **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions**.
   * Crea dos *Repository Secrets*:
     * `NOTION_TOKEN`: Tu token de Notion (`ntn_...`).
     * `NOTION_DATABASE_ID`: Tu ID de base de datos (`3dad69b2-133a-8159-bc99-c4a4b9ff5db7`).
4. **Listo:** La acción se ejecutará sola cada semana o puedes forzarla cuando quieras desde la pestaña **Actions** $\rightarrow$ **Run workflow**.

---

## 🎯 Playbook de Ventas & Funnel de Prospección

Consulta el archivo **[FUNNEL_PROSPECCION.md](file:///Users/josewilliamszegarra/Desktop/Sistema%20Captura%20de%20Clientes/FUNNEL_PROSPECCION.md)** para acceder a:
* Guiones de WhatsApp probados para no sonar como spam.
* Cadencia de seguimiento a 14 días (el dinero está en el follow-up).
* Estructura de la llamada de cierre de 15 minutos.
* Rutina diaria de 20 minutos para gestionar prospectos desde el móvil.

---

## 📊 Datos de Demostración Capturados (Chiclayo)

1. **ESCO S.A.C. - Estudio de Arquitectura**: `+51 923 225 227` | `ESPINOZA.CORPORATION.SAC@GMAIL.COM` | [esco.com.pe](https://www.esco.com.pe)
2. **Vive Más Arquitectos**: `+51 979 649 678` | `vivemas380@gmail.com` | Calle Los Sauces, Chiclayo
3. **CONSIZAC**: `+51 945 293 512` | `contacto@consizac.pe` | [consizac.pe](https://consizac.pe)
4. **MC Constructora & Arquitectura**: `+51 979 667 008` | `contacto@mcconstructora.com` | [mcconstructora.com](https://www.mcconstructora.com)
5. **ARQA - Claudia Lau Arquitecta**: `+51 904 349 875` | `informes.arqa@gmail.com` | [claudialauarquitecta.com](https://www.claudialauarquitecta.com/)

---

## 🛠️ Comandos Útiles

* **Regenerar CSV y JSON:**
  ```bash
  python3 seed_leads.py
  ```
* **Probar normalizador telefónico y WhatsApp:**
  ```bash
  python3 lead_capture.py
  ```
* **Verificar estado de Notion:**
  ```bash
  python3 notion_crm.py
  ```
