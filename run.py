import eventlet
eventlet.monkey_patch()

from flask import Flask, request, session, redirect, url_for, flash
import os

app = Flask(__name__)
app.secret_key = 'clave-secreta-para-desarrollo'

# ============================================
# LOGIN SIMPLE - SIN BASE DE DATOS
# ============================================

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SÍG Transporte</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 0; background: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .container { max-width: 400px; padding: 40px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
            h1 { color: #1a73e8; }
            .input-group { margin: 15px 0; text-align: left; }
            .input-group label { display: block; margin-bottom: 5px; color: #555; }
            .input-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; box-sizing: border-box; }
            .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
            .btn:hover { background: #1557b0; }
            .error { color: red; margin: 10px 0; padding: 10px; background: #ffebee; border-radius: 5px; }
            .info { background: #e8f0fe; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .info p { margin: 5px 0; }
            .footer { color: #999; font-size: 12px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚌 SÍG Transporte</h1>
            <h2 style="color:#666;font-size:18px;">Panel de Administración</h2>
            
            <div class="info">
                <p><strong>Usuario:</strong> 00000001</p>
                <p><strong>Contraseña:</strong> admin123</p>
            </div>
            
            <form method="POST" action="/login">
                <div class="input-group">
                    <label>Número de CI</label>
                    <input type="text" name="ci" placeholder="00000001" required>
                </div>
                <div class="input-group">
                    <label>Contraseña</label>
                    <input type="password" name="password" placeholder="Ingresa tu contraseña" required>
                </div>
                <button type="submit" class="btn">Ingresar</button>
            </form>
            
            <p class="footer">Solo personal autorizado (Admin / Autoridad)<br>El acceso de choferes y pasajeros es desde la app móvil</p>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['POST'])
def login():
    ci = request.form.get('ci')
    password = request.form.get('password')
    
    # Credenciales fijas
    if ci == '00000001' and password == 'admin123':
        session['user_id'] = 1
        session['user_ci'] = '00000001'
        session['user_rol'] = 'admin'
        session['user_nombre'] = 'Administrador'
        return redirect(url_for('dashboard'))
    else:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error de Login</title>
            <style>
                body { font-family: Arial; margin: 50px; background: #f0f2f5; text-align: center; }
                .container { max-width: 400px; margin: 0 auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .error { color: red; background: #ffebee; padding: 15px; border-radius: 5px; border: 2px solid red; }
                .btn { display: inline-block; padding: 10px 20px; background: #1a73e8; color: white; text-decoration: none; border-radius: 5px; margin-top: 15px; }
                .info { background: #e8f0fe; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚌 SÍG Transporte</h1>
                <div class="error">
                    <h3>❌ Credenciales incorrectas</h3>
                </div>
                <div class="info">
                    <p><strong>Usuario correcto:</strong> 00000001</p>
                    <p><strong>Contraseña correcta:</strong> admin123</p>
                </div>
                <a href="/" class="btn">Volver a intentar</a>
            </div>
        </body>
        </html>
        '''

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - SÍG Transporte</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 0; background: #f0f2f5; }
            .header { background: #1a73e8; color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { margin: 0; }
            .header a { color: white; text-decoration: none; padding: 8px 16px; background: rgba(255,255,255,0.2); border-radius: 5px; }
            .header a:hover { background: rgba(255,255,255,0.3); }
            .container { max-width: 1200px; margin: 20px auto; padding: 20px; }
            .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
            .card h2 { margin-top: 0; color: #1a73e8; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
            .stat { background: white; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .stat h3 { margin: 0; color: #666; font-size: 14px; }
            .stat .number { font-size: 32px; font-weight: bold; color: #1a73e8; margin: 10px 0; }
            .menu { display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }
            .menu a { padding: 12px 20px; background: #e8f0fe; color: #1a73e8; text-decoration: none; border-radius: 5px; }
            .menu a:hover { background: #d2e3fc; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚌 SÍG Transporte</h1>
            <div>
                <span>👤 Administrador (00000001)</span>
                <a href="/logout">Cerrar sesión</a>
            </div>
        </div>
        
        <div class="container">
            <div class="card">
                <h2>📊 Panel de Administración</h2>
                <p style="color:green;font-weight:bold;">✅ ¡Bienvenido al sistema de gestión de transporte!</p>
            </div>
            
            <div class="grid">
                <div class="stat">
                    <h3>👥 Usuarios</h3>
                    <div class="number">1</div>
                </div>
                <div class="stat">
                    <h3>🚌 Conductores</h3>
                    <div class="number">0</div>
                </div>
                <div class="stat">
                    <h3>🚗 Vehículos</h3>
                    <div class="number">0</div>
                </div>
                <div class="stat">
                    <h3>🗺️ Rutas</h3>
                    <div class="number">0</div>
                </div>
            </div>
            
            <div class="card">
                <h2>⚙️ Acciones Rápidas</h2>
                <div class="menu">
                    <a href="/usuarios">👥 Usuarios</a>
                    <a href="/conductores">👨‍✈️ Conductores</a>
                    <a href="/vehiculos">🚗 Vehículos</a>
                    <a href="/rutas">🗺️ Rutas</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/logout')
def logout():
    session.clear()
    return '<h1>✅ Sesión cerrada</h1><a href="/">Volver al login</a>'

@app.route('/usuarios')
def usuarios():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return '''
    <h1>👥 Gestión de Usuarios</h1>
    <table border="1" style="border-collapse:collapse;width:100%;">
        <tr><th>CI</th><th>Nombre</th><th>Rol</th><th>Estado</th></tr>
        <tr><td>00000001</td><td>Administrador</td><td>Admin</td><td>✅ Activo</td></tr>
    </table>
    <p><a href="/dashboard">Volver</a></p>
    '''

@app.route('/conductores')
def conductores():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return '<h1>🚧 Conductores - En construcción</h1><a href="/dashboard">Volver</a>'

@app.route('/vehiculos')
def vehiculos():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return '<h1>🚧 Vehículos - En construcción</h1><a href="/dashboard">Volver</a>'

@app.route('/rutas')
def rutas():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return '<h1>🚧 Rutas - En construcción</h1><a href="/dashboard">Volver</a>'

# ============================================
# EJECUTAR
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
