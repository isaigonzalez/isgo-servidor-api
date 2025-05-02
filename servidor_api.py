from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import psycopg2
from psycopg2.extras import Json
import json
from datetime import datetime

app = FastAPI()

AGENT_SECRET = "isgo123"

# 🔐 Configuración de conexión a PostgreSQL
DB_HOST = "dpg-d0a6sejuibrs73b5p8hg-a.oregon-postgres.render.com"
DB_PORT = "5432"
DB_NAME = "bienes"
DB_USER = "bienes_user"
DB_PASS = "xpQEaq9az2Epj5iT8nS3OBliMreSFuRA"  # ← tu contraseña real aquí

# Función para guardar en PostgreSQL
def guardar_en_postgres(datos_json):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO equipos (fecha_reporte, datos) VALUES (%s, %s);",
            (datetime.now(), Json(datos_json))
        )
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Reporte guardado en PostgreSQL")
    except Exception as e:
        print("❌ Error al guardar en PostgreSQL:", e)

# 📨 Ruta que el agente necesita: RECIBE reportes
# Ruta protegida
@app.post("/reporte")
async def recibir_reporte(request: Request):
    token_recibido = request.headers.get("Authorization")

    if token_recibido != f"Bearer {AGENT_SECRET}":
        return JSONResponse(status_code=401, content={"mensaje": "No autorizado"})

    datos = await request.json()
    guardar_en_postgres(datos)
    return {"mensaje": "✅ Reporte guardado exitosamente"}

# 🌐 Ruta del dashboard visual: MUESTRA reportes
@app.get("/reportes", response_class=HTMLResponse)
async def ver_reportes():
    html = """
    <html>
        <head>
            <title>Dashboard de Reportes</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Dashboard de Equipos Reportados</h1>
            <table>
                <tr>
                    <th>Fecha</th>
                    <th>Hostname</th>
                    <th>IP Local</th>
                    <th>Sistema Operativo</th>
                    <th>RAM (GB)</th>
                    <th>CPU</th>
                    <th>Fabricante CPU</th>
                    <th>Familia CPU</th>
                    <th>Batería</th>
                    <th>Antivirus</th>
                </tr>
    """

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()
        cur.execute("SELECT fecha_reporte, datos FROM equipos ORDER BY fecha_reporte DESC;")
        registros = cur.fetchall()

        for fecha, datos in registros:
            html += f"""
            <tr>
                <td>{fecha.strftime("%Y-%m-%d %H:%M:%S")}</td>
                <td>{datos.get('hostname', 'N/A')}</td>
                <td>{datos.get('ip_local', 'N/A')}</td>
                <td>{datos.get('sistema_operativo', 'N/A')}</td>
                <td>{datos.get('ram_total_gb', 'N/A')}</td>
                <td>{datos.get('cpu', {}).get('nombre_cpu', 'N/A')}</td>
                <td>{datos.get('cpu', {}).get('fabricante', 'N/A')}</td>
                <td>{datos.get('cpu', {}).get('familia', 'N/A')}</td>
                <td>{datos.get('bateria_porcentaje', 'N/A')}</td>
                <td>{datos.get('antivirus', 'N/A')}</td>
            </tr>
            """

        cur.close()
        conn.close()
    except Exception as e:
        html += f"<tr><td colspan='10'>❌ Error al cargar reportes: {e}</td></tr>"

    html += """
            </table>
        </body>
    </html>
    """
    return HTMLResponse(content=html)
