# ===== CÓDIGO TEMPORAL PARA RESETEAR CONTRASEÑA =====
# ELIMINAR DESPUÉS DE USAR
@app.route('/reset-admin')
def reset_admin():
    import sqlite3
    import os
    try:
        # Buscar la base de datos
        db_path = 'instance/transporte.db'
        if not os.path.exists(db_path):
            db_path = 'transporte.db'
            if not os.path.exists(db_path):
                return "❌ No se encontró la base de datos"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si existe la tabla usuario
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuario'")
        if not cursor.fetchone():
            return "❌ Tabla 'usuario' no existe"
        
        # Actualizar contraseña
        cursor.execute("UPDATE usuario SET password = 'admin123' WHERE ci = '00000001'")
        
        if cursor.rowcount == 0:
            # Si no existe, crearlo
            cursor.execute("INSERT INTO usuario (ci, password, rol) VALUES ('00000001', 'admin123', 'admin')")
            conn.commit()
            return "✅ Usuario ADMIN creado: CI=00000001, Password=admin123"
        else:
            conn.commit()
            return "✅ Contraseña actualizada: CI=00000001, Password=admin123"
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/ver-usuarios')
def ver_usuarios():
    import sqlite3
    import os
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
# ===== FIN CÓDIGO TEMPORAL =====
