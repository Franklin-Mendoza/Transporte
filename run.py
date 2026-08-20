import os
from flask import Flask

# Crear la aplicación
app = Flask(__name__)

# ============================================
# RUTA PRINCIPAL - MUESTRA LAS CREDENCIALES
# ============================================

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SÍG Transporte</title>
        <style>
            body { font-family: Arial; margin: 50px; background: #f0f2f5; }
            .container { max-width: 500px; margin: 0 auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
            h1 { color: #1a73e8; }
            .credenciales { background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #4caf50; }
            .credenciales h3 { color: #2e7d32; margin: 0 0 10px 0; }
            .btn { display: inline-block; padding: 12px 30px; background: #1a73e8; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; }
            .btn:hover { background: #1557b0; }
            .error { color: red; }
            .success { color: green; }
            .info { color: #666; font-size: 12px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚌 SÍG Transporte</h1>
            <h2>🔐 RECUPERACIÓN DE CONTRASEÑA</h2>
            
            <div class="credenciales">
                <h3>✅ CREDENCIALES DE ACCESO</h3>
                <p style="font-size:18px;"><strong>Usuario:</strong> <span style="color:#1a73e8;">00000001</span></p>
                <p style="font-size:18px;"><strong>Contraseña:</strong> <span style="color:#1a73e8;">admin123</span></p>
            </div>
            
            <p>
                <a href="/reset" class="btn">🔄 Restablecer Contraseña</a>
            </p>
            
            <p class="info">Solo personal autorizado (Admin / Autoridad)</p>
            <p class="info">El acceso de choferes y pasajeros es desde la app móvil</p>
        </div>
    </body>
    </html>
    '''

@app.route('/reset')
def reset():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Contraseña Restablecida</title>
        <style>
            body { font-family: Arial; margin: 50px; background: #f0f2f5; }
            .container { max-width: 500px; margin: 0 auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
            h1 { color: #1a73e8; }
            .success { background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #4caf50; }
            .success h3 { color: #2e7d32; margin: 0; }
            .btn { display: inline-block; padding: 12px 30px; background: #1a73e8; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; }
            .btn:hover { background: #1557b0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚌 SÍG Transporte</h1>
            <div class="success">
                <h3>✅ CONTRASEÑA RESTABLECIDA</h3>
                <p><strong>Usuario:</strong> 00000001</p>
                <p><strong>Contraseña:</strong> admin123</p>
            </div>
            <a href="/" class="btn">Volver al inicio</a>
        </div>
    </body>
    </html>
    '''

@app.route('/admin')
def admin():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Panel de Administración</title>
        <style>
            body { font-family: Arial; margin: 50px; background: #f0f2f5; }
            .container { max-width: 600px; margin: 0 auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #1a73e8; }
            .menu { display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0; }
            .menu a { flex: 1; min-width: 120px; padding: 15px; background: #e8f0fe; color: #1a73e8; text-decoration: none; border-radius: 5px; text-align: center; }
            .menu a:hover { background: #d2e3fc; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚌 SÍG Transporte</h1>
            <h2>Panel de Administración</h2>
            <div style="background:#e8f5e9;padding:15px;border-radius:5px;border:2px solid #4caf50;">
                <p><strong>✅ Sesión iniciada como:</strong> Administrador (00000001)</p>
            </div>
            <div class="menu">
                <a href="/">📊 Dashboard</a>
                <a href="/reset">🔄 Resetear</a>
            </div>
            <p style="color:#666;font-size:12px;margin-top:20px;">Solo personal autorizado</p>
        </div>
    </body>
    </html>
    '''

# ============================================
# EJECUTAR LA APLICACIÓN
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
