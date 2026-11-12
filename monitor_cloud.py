import os
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def conectar_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=os.getenv("DB_PORT", "5432")
    )

def consultar_open_meteo(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code",
        "hourly": "temperature_2m,precipitation,precipitation_probability,wind_speed_10m",
        "forecast_hours": 12,
        "timezone": "America/Bogota"
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    
    hourly = data["hourly"]
    return {
        "temp_actual": data["current"]["temperature_2m"],
        "codigo_clima": data["current"]["weather_code"],
        "temp_max_12h": max(hourly["temperature_2m"]),
        "lluvia_acum_12h": round(sum(hourly["precipitation"]), 2),
        "prob_lluvia_max": max(hourly["precipitation_probability"]),
        "viento_max_12h": max(hourly["wind_speed_10m"])
    }

def calcular_promedios_7d(cursor, zona_id):
    query = """
        SELECT 
            COALESCE(AVG(temp_max_pronostico), 0) AS avg_temp,
            COALESCE(AVG(precipitacion_mm), 0) AS avg_lluvia
        FROM lecturas_clima
        WHERE zona_id = %s 
          AND fecha_ejecucion >= NOW() - INTERVAL '7 days'
    """
    cursor.execute(query, (zona_id,))
    row = cursor.fetchone()
    return float(row[0]), float(row[1])

def evaluar_riesgo(datos, zona, avg_temp, avg_lluvia):
    # zona es un diccionario gracias a RealDictCursor o acceso por clave
    alertas = []
    nivel = "BAJO"

    if datos["lluvia_acum_12h"] >= float(zona["umbral_lluvia_mm"]):
        alertas.append(f"Lluvia fuerte proyectada ({datos['lluvia_acum_12h']} mm)")
        nivel = "ALTO"
    elif datos["prob_lluvia_max"] >= 70:
        alertas.append(f"Alta prob. de precipitación ({datos['prob_lluvia_max']}%)")
        nivel = "MODERADO" if nivel == "BAJO" else nivel

    if datos["viento_max_12h"] >= float(zona["umbral_viento_kmh"]):
        alertas.append(f"Ráfagas de viento ({datos['viento_max_12h']} km/h)")
        nivel = "ALTO"

    if datos["temp_max_12h"] >= float(zona["umbral_temp_max"]):
        alertas.append(f"Estrés térmico ({datos['temp_max_12h']} °C)")
        nivel = "MODERADO" if nivel == "BAJO" else nivel

    delta_temp = round(datos["temp_max_12h"] - avg_temp, 2) if avg_temp > 0 else 0.0
    delta_lluvia = round(datos["lluvia_acum_12h"] - avg_lluvia, 2) if avg_lluvia > 0 else 0.0

    return nivel, alertas, delta_temp, delta_lluvia

def enviar_telegram(mensaje):
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "HTML"}
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()

def ejecutar_pipeline():
    conn = conectar_db()
    cursor = conn.cursor()
    ahora = datetime.now()

    # Consultar zonas activas
    cursor.execute("""
        SELECT id, nombre, descripcion, latitud, longitud, 
               umbral_lluvia_mm, umbral_viento_kmh, umbral_temp_max 
        FROM zonas_monitoreo WHERE activo = TRUE
    """)
    rows = cursor.fetchall()
    
    # Mapear a diccionarios para mayor claridad
    zonas = []
    for r in rows:
        zonas.append({
            "id": r[0], "nombre": r[1], "descripcion": r[2],
            "latitud": float(r[3]), "longitud": float(r[4]),
            "umbral_lluvia_mm": r[5], "umbral_viento_kmh": r[6], "umbral_temp_max": r[7]
        })

    lineas_reporte = [
        f"<b>📊 BOLETÍN DE RIESGO LOGÍSTICO (NORTE DE SANTANDER)</b>",
        f"<i>Corte: {ahora.strftime('%Y-%m-%d %H:%M')} (Ventana 12h)</i>\n"
    ]

    for zona in zonas:
        datos = consultar_open_meteo(zona["latitud"], zona["longitud"])
        avg_temp, avg_lluvia = calcular_promedios_7d(cursor, zona["id"])
        nivel, alertas, delta_temp, delta_lluvia = evaluar_riesgo(datos, zona, avg_temp, avg_lluvia)

        # Insertar lectura en Supabase
        insert_sql = """
            INSERT INTO lecturas_clima (
                zona_id, fecha_ejecucion, temp_actual, temp_max_pronostico,
                precipitacion_mm, probabilidad_lluvia_pct, viento_max_kmh,
                codigo_clima, delta_temp_7d, delta_lluvia_7d, nivel_riesgo
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (
            zona["id"], ahora, datos["temp_actual"], datos["temp_max_12h"],
            datos["lluvia_acum_12h"], datos["prob_lluvia_max"], datos["viento_max_12h"],
            datos["codigo_clima"], delta_temp, delta_lluvia, nivel
        ))

        icono = {"BAJO": "🟢", "MODERADO": "🟡", "ALTO": "🔴"}[nivel]
        signo_t = "+" if delta_temp >= 0 else ""
        
        bloque = (
            f"{icono} <b>{zona['nombre']}</b> — Riesgo: <b>{nivel}</b>\n"
            f"   • Temp Máx: {datos['temp_max_12h']}°C ({signo_t}{delta_temp}°C vs prom. 7d)\n"
            f"   • Lluvia est.: {datos['lluvia_acum_12h']} mm (Prob: {datos['prob_lluvia_max']}%)\n"
            f"   • Viento máx.: {datos['viento_max_12h']} km/h\n"
        )
        if alertas:
            bloque += f"   ⚠️ <i>Acción sugerida: {', '.join(alertas)}</i>\n"
        
        lineas_reporte.append(bloque)

    lineas_reporte.append("—\n<i>Pipeline Cloud: GitHub Actions + Supabase + Open-Meteo</i>")
    mensaje_final = "\n".join(lineas_reporte)

    try:
        enviar_telegram(mensaje_final)
        cursor.execute(
            "INSERT INTO historial_reportes (resumen_enviado, estado_envio) VALUES (%s, 'ENVIADO')",
            (mensaje_final,)
        )
    except Exception as e:
        cursor.execute(
            "INSERT INTO historial_reportes (resumen_enviado, estado_envio, detalle_error) VALUES (%s, 'ERROR', %s)",
            (mensaje_final, str(e)[:250])
        )
        raise
    finally:
        conn.commit()
        cursor.close()
        conn.close()

if __name__ == "__main__":
    ejecutar_pipeline()