from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import psycopg2
from psycopg2.extras import Json
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
    except Exception as e:
        print("❌ Error al guardar en PostgreSQL:", e)

@app.post("/reporte")
async def recibir_reporte(request: Request):
    token_recibido = request.headers.get("Authorization")
    if token_recibido != f"Bearer {AGENT_SECRET}":
        return JSONResponse(status_code=401, content={"mensaje": "No autorizado"})
    datos = await request.json()
    guardar_en_postgres(datos)
    return {"mensaje": "✅ Reporte guardado exitosamente"}

@app.get("/reportes", response_class=HTMLResponse)
async def ver_reportes(request: Request):
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
        cur.close()
        conn.close()

        datos_procesados = []
        for fecha, datos in registros:
            datos_procesados.append([
                fecha.strftime("%Y-%m-%d %H:%M:%S"),
                datos.get('hostname', 'N/A'),
                datos.get('ip_local', 'N/A'),
                datos.get('sistema_operativo', 'N/A'),
                datos.get('ram_total_gb', 'N/A'),
                datos.get('cpu', {}).get('nombre_cpu', 'N/A'),
                datos.get('cpu', {}).get('fabricante', 'N/A'),
                datos.get('cpu', {}).get('familia', 'N/A'),
                datos.get('bateria_porcentaje', 'N/A'),
                datos.get('antivirus', 'N/A')
            ])

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "datos": datos_procesados
        })
    except Exception as e:
        return HTMLResponse(f"<h1>Error al cargar reportes: {e}</h1>")
