import os
from flask import Flask

# ============================================
# CREAR LA APLICACIÓN
# ============================================

app = Flask(__name__)

# ============================================
# RUTAS
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

# ============================================
# ESTO ES OBLIGATORIO PARA QUE RENDER FUNCIONE
# ============================================

# La variable 'app' ya está definida arriba
# Gunicorn la usará para ejecutar la aplicación

# ============================================
# SOLO PARA EJECUCIÓN LOCAL
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
