# 🌦️ Monitor de Riesgo Logístico y Operativo — Norte de Santander

Pipeline ETL automatizado en la nube que extrae pronósticos meteorológicos en tiempo real, almacena registros históricos en PostgreSQL y emite boletines ejecutivos de alerta temprana vía Telegram para optimizar la toma de decisiones logísticas en corredores estratégicos de **Norte de Santander, Colombia** (Cúcuta, Pamplona y Chinácota).

---

## 🎯 Problema de Negocio que Resuelve

En sectores como transporte de carga, distribución comercial, agroindustria y construcción en regiones con topografía compleja (como el corredor vial Cúcuta – Pamplona), las variaciones climáticas repentinas generan retrasos operativos, sobrecostos logísticos y riesgos de seguridad vial.

Este sistema elimina la revisión manual dispersa mediante una **arquitectura Serverless de costo $0**, entregando información accionable directamente en los canales de comunicación del equipo operativo antes del inicio y cierre de cada jornada.

---

## 🏗️ Arquitectura del Sistema
```text
[ Open-Meteo API ] ──(Extracción JSON)──▶ [ Python ETL Script ]
                                                  │
                       ┌──────────────────────────┴──────────────────────────┐
                       ▼                                                     ▼
        [ PostgreSQL / Supabase ]                             [ Telegram Bot API ]
      (Persistencia Histórica IPv4)                        (Boletín Ejecutivo en Canal)
                       ▲                                                     ▲
                       └──────────────────────────┬──────────────────────────┘
                                                  │
                                     [ GitHub Actions (Cron) ]
                                    (Ejecución 06:00 y 18:00 COT)
```

---

### Stack Tecnológico
* **Lenguaje:** Python 3.11 (`requests`, `psycopg2-binary`, `python-dotenv`)
* **Fuente de Datos:** Open-Meteo API (datos meteorológicos de alta precisión sin dependencia de llaves de pago).
* **Base de Datos:** PostgreSQL alojado en **Supabase** (conectividad optimizada mediante *Session Pooler* IPv4).
* **Orquestación y CI/CD:** **GitHub Actions** con ejecución programada (`cron`) cada 12 horas y soporte para disparo manual (`workflow_dispatch`).
* **Notificaciones:** Telegram Bot API integrado a canal de difusión operativo.

---

## 📍 Cobertura Geográfica Monitoreada

| Municipio / Nodo | Rol Operativo | Variables Evaluadas |
| :--- | :--- | :--- |
| **Cúcuta** | Hub comercial, fronterizo y centro de distribución | Temperatura, precipitación, viento y condición |
| **Pamplona** | Nodo vial crítico de alta montaña y tránsito nacional | Temperatura, precipitación, viento y condición |
| **Chinácota** | Corredor agroindustrial y ruta alterna regional | Temperatura, precipitación, viento y condición |

---

## ⚙️ Despliegue y Configuración

1. **Clonar el repositorio:**
   `git clone https://github.com/WilliamAngaritaRomero/ReporteClima.git`
   `cd ReporteClima`

2. **Instalar dependencias:**
   `pip install -r requirements.txt`

3. **Configurar Variables de Entorno:**
   Crea un archivo `.env` en la raíz del proyecto (para ejecución local) o configura los siguientes **Repository Secrets** en GitHub (`Settings > Secrets and variables > Actions`):
   * `DB_HOST`: Host del Session Pooler de Supabase
   * `DB_NAME`: `postgres`
   * `DB_USER`: Usuario del proyecto en Supabase
   * `DB_PASSWORD`: Contraseña de la base de datos
   * `DB_PORT`: `5432`
   * `TELEGRAM_TOKEN`: Token generado por `@BotFather`
   * `TELEGRAM_CHAT_ID`: Identificador del canal público (ej. `@monitorclima`)

4. **Ejecución Manual o Programada:**
   * **Local:** `python monitor_cloud.py`
   * **Nube:** El flujo `.github/workflows/monitor_clima.yml` se ejecuta automáticamente todos los días a las **06:00 AM** y **06:00 PM** hora Colombia (`11:00` y `23:00` UTC).

---

## 📈 Escalabilidad Futura (Roadmap)
* [ ] Integración de umbrales dinámicos de alerta crítica (ej. lluvias > 15 mm/h o ráfagas de viento) con notificaciones prioritarias.
* [ ] Dashboard analítico en tiempo real conectado a Supabase para visualizar tendencias históricas de precipitación por corredor.
* [ ] Expansión de cobertura hacia otros nodos logísticos de Santander y frontera.

---

**Desarrollado por [William Angarita Romero](https://github.com/WilliamAngaritaRomero)** — *Ingeniería de Automatización, Integración de Sistemas y Desarrollo Full-Stack.*  
*Arquitectura diseñada e implementada con asistencia técnica de **Gemini (Google AI)** para la optimización del pipeline ETL, integración de infraestructura en la nube y documentación.*
