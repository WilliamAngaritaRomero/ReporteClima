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
