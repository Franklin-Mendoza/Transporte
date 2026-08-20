import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, session
import sqlite3
import os

# ============================================
# APP SIMPLE PARA RECUPERAR CONTRASEÑA
# ============================================

app = Flask(__name__)
app.secret_key = 'clave-secreta-para-desarrollo'

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SÍG Transporte - Recuperación</title>
        <style>
            body { font-family: Arial; margin: 50px; background: #f0f2f5; }
            .container { max-width: 600px; margin: 0 auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #1a73e8; }
            .btn { display: inline-block; padding: 10px 20px; margin: 5px; background: #1a73e8; color: white; text-decoration: none; border-radius: 5px; }
            .btn:hover { background: #1557b0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚌 SÍG Transporte</h1>
            <h2>🔐 Recuperación de Contraseña</h2>
            <div style="background:#e8f0fe;padding:15px;border-radius:5px;margin:20px 0;">
                <p><strong>Usuario:</strong> 00000001</p>
                <p><strong>Contraseña:</strong> admin123</p>
            </div>
            <hr>
            <p>
                <a href="/reset-admin" class="btn">🔄 Restablecer</a>
                <a href="/ver-tablas" class="btn">📊 Ver Tablas</a>
                <a href="/crear-admin" class="btn">➕ Crear Admin</a>
                <a href="/ver-usuarios" class="btn">👥 Ver Usuarios</a>
            </p>
            <hr>
            <p style="color:#666;font-size:12px;">Solo personal autorizado (Admin / Autoridad)</p>
        </div>
    </body>
    </html>
    '''

@app.route('/ver-tablas')
def ver_tablas():
    try:
        db_path = 'instance/transporte.db'
        if not os.path.exists(db_path):
            db_path = 'transporte.db'
        
        if not os.path.exists(db_path):
            return f"❌ No se encontró la base de datos en: {db_path}"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cursor.fetchall()
        
        html = "<h2>📊 Tablas encontradas:</h2><ul>"
        for t in tablas:
            nombre = t[0]
            cursor.execute(f"PRAGMA table_info({nombre})")
            columnas = [col[1] for col in cursor.fetchall()]
            cursor.execute(f"SELECT COUNT(*) FROM {nombre}")
            count = cursor.fetchone()[0]
            html += f"<li><b>{nombre}</b> ({count} registros) - Columnas: {', '.join(columnas)}</li>"
        html += "</ul>"
        conn.close()
        return html
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/ver-usuarios')
def ver_usuarios():
    try:
        db_path = 'instance/transporte.db'
        if not os.path.exists(db_path):
            db_path = 'transporte.db'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cursor.fetchall()
        
        resultado = "<h2>👥 Usuarios en el sistema</h2>"
        
        for t in tablas:
            nombre = t[0]
            if nombre.lower() in ['usuario', 'admin', 'usuarios', 'user']:
                cursor.execute(f"SELECT * FROM {nombre}")
                datos = cursor.fetchall()
                cursor.execute(f"PRAGMA table_info({nombre})")
                columnas = [col[1] for col in cursor.fetchall()]
                
                resultado += f"<h3>Tabla: {nombre}</h3>"
                resultado += f"<p>Columnas: {', '.join(columnas)}</p>"
                resultado += f"<p>Total: {len(datos)} usuarios</p>"
                
                if datos:
                    resultado += "<ul>"
                    for d in datos:
                        resultado += f"<li>{d}</li>"
                    resultado += "</ul>"
        
        conn.close()
        
        if "Tabla:" not in resultado:
            resultado += f"<p>❌ No se encontró tabla de usuarios. Tablas: {[t[0] for t in tablas]}</p>"
        
        return resultado
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/reset-admin')
def reset_admin():
    try:
        db_path = 'instance/transporte.db'
        if not os.path.exists(db_path):
            db_path = 'transporte.db'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cursor.fetchall()
        
        tabla_usuario = None
        for t in tablas:
            nombre = t[0]
            if nombre.lower() in ['usuario', 'admin', 'usuarios', 'user']:
                tabla_usuario = nombre
                break
        
        if not tabla_usuario:
            return f"❌ No hay tabla de usuarios. Tablas: {[t[0] for t in tablas]}"
        
        cursor.execute(f"PRAGMA table_info({tabla_usuario})")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'ci' in columnas and 'password' in columnas:
            cursor.execute(f"UPDATE {tabla_usuario} SET password = 'admin123' WHERE ci = '00000001'")
            
            if cursor.rowcount == 0:
                if 'rol' in columnas:
                    cursor.execute(f"INSERT INTO {tabla_usuario} (ci, password, rol) VALUES ('00000001', 'admin123', 'admin')")
                else:
                    cursor.execute(f"INSERT INTO {tabla_usuario} (ci, password) VALUES ('00000001', 'admin123')")
                mensaje = "✅ Usuario ADMIN creado"
            else:
                mensaje = "✅ Contraseña actualizada"
            
            conn.commit()
            conn.close()
            return f"{mensaje} en tabla '{tabla_usuario}'<br><br>Usuario: <b>00000001</b><br>Contraseña: <b>admin123</b>"
        else:
            return f"❌ La tabla {tabla_usuario} no tiene columnas 'ci' o 'password'. Columnas: {columnas}"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/crear-admin')
def crear_admin():
    try:
        db_path = 'instance/transporte.db'
        if not os.path.exists(db_path):
            db_path = 'transporte.db'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cursor.fetchall()
        
        tabla_usuario = None
        for t in tablas:
            nombre = t[0]
            if nombre.lower() in ['usuario', 'admin', 'usuarios', 'user']:
                tabla_usuario = nombre
                break
        
        if not tabla_usuario:
            return f"❌ No hay tabla de usuarios. Tablas: {[t[0] for t in tablas]}"
        
        cursor.execute(f"PRAGMA table_info({tabla_usuario})")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'ci' in columnas and 'password' in columnas:
            cursor.execute(f"DELETE FROM {tabla_usuario} WHERE ci = '00000001'")
            
            if 'rol' in columnas:
                cursor.execute(f"INSERT INTO {tabla_usuario} (ci, password, rol) VALUES ('00000001', 'admin123', 'admin')")
            else:
                cursor.execute(f"INSERT INTO {tabla_usuario} (ci, password) VALUES ('00000001', 'admin123')")
            
            conn.commit()
            conn.close()
            return f"✅ Admin creado en tabla '{tabla_usuario}'<br><br>Usuario: <b>00000001</b><br>Contraseña: <b>admin123</b>"
        else:
            return f"❌ La tabla {tabla_usuario} no tiene columnas 'ci' o 'password'"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================
# EJECUTAR APLICACIÓN
# ============================================

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    app.run(host=host, port=port, debug=False)
