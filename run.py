import eventlet
eventlet.monkey_patch()

from app import create_app, socketio
import os
import sqlite3

app = create_app()

# ============================================
# RUTA TEMPORAL PARA VER LA BASE DE DATOS
# ============================================

@app.route('/ver-db')
def ver_db():
    try:
        import os
        import sqlite3
        
        # Buscar la base de datos
        rutas = ['instance/transporte.db', 'transporte.db', '/opt/render/project/src/instance/transporte.db']
        encontrada = None
        
        for r in rutas:
            if os.path.exists(r):
                encontrada = r
                break
        
        if not encontrada:
            return "❌ No se encontró la base de datos"
        
        conn = sqlite3.connect(encontrada)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cursor.fetchall()
        
        html = f"<h2>📊 Base de datos encontrada en: {encontrada}</h2>"
        html += "<h3>Tablas:</h3><ul>"
        for t in tablas:
            html += f"<li>{t[0]}</li>"
        html += "</ul>"
        
        # Ver usuarios
        for t in tablas:
            if t[0].lower() in ['usuario', 'admin', 'usuarios', 'user']:
                cursor.execute(f"SELECT * FROM {t[0]}")
                datos = cursor.fetchall()
                html += f"<h3>Usuarios en '{t[0]}':</h3><ul>"
                for d in datos:
                    html += f"<li>{d}</li>"
                html += "</ul>"
        
        conn.close()
        return html
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    socketio.run(app, host=host, port=port, debug=debug)
