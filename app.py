from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# ============================================
# CÓDIGO PARA RECUPERAR CONTRASEÑA - TEMPORAL
# ============================================

@app.route('/reset-admin')
def reset_admin():
    try:
        # Buscar la base de datos
        db_path = 'instance/transporte.db'
        if not os.path.exists(db_path):
            db_path = 'transporte.db'
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Intentar actualizar contraseña
        cursor.execute("UPDATE usuario SET password = 'admin123' WHERE ci = '00000001'")
        
        if cursor.rowcount == 0:
            # Si no existe, crearlo
            cursor.execute("INSERT INTO usuario (ci, password, rol) VALUES ('00000001', 'admin123', 'admin')")
            conn.commit()
            return "✅ USUARIO CREADO: CI=00000001, Password=admin123"
        else:
            conn.commit()
            return "✅ CONTRASEÑA ACTUALIZADA: CI=00000001, Password=admin123"
            
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
        cursor.execute("SELECT ci, password, rol FROM usuario")
        usuarios = cursor.fetchall()
        conn.close()
        
        if not usuarios:
            return "❌ No hay usuarios en la base de datos"
        
        html = "<h2>Usuarios en el sistema:</h2><ul>"
        for u in usuarios:
            html += f"<li>CI: {u[0]} - Password: {u[1]} - Rol: {u[2]}</li>"
        html += "</ul>"
        return html
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================
# FIN CÓDIGO TEMPORAL
# ============================================

# Ruta principal - login
@app.route('/')
def index():
    return '''
    <h1>SÍG Transporte</h1>
    <h2>Panel de Administración</h2>
    <p>Usuario: 00000001</p>
    <p>Contraseña: admin123</p>
    <a href="/reset-admin">Restablecer contraseña</a> | 
    <a href="/ver-usuarios">Ver usuarios</a>
    '''

if __name__ == '__main__':
    app.run(debug=True)
