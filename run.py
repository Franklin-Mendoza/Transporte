import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SÍG Transporte</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f0f2f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                text-align: center;
                max-width: 450px;
            }
            h1 { color: #1a73e8; margin-top: 0; }
            .credenciales {
                background: #e8f5e9;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border: 2px solid #4caf50;
            }
            .credenciales h3 { color: #2e7d32; margin: 0 0 10px 0; }
            .credenciales p { font-size: 18px; margin: 8px 0; }
            .credenciales span { color: #1a73e8; font-weight: bold; }
            .footer { color: #999; font-size: 12px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚌 SÍG Transporte</h1>
            <h2 style="color:#666;">🔐 Recuperación de Contraseña</h2>
            
            <div class="credenciales">
                <h3>✅ CREDENCIALES DE ACCESO</h3>
                <p><strong>Usuario:</strong> <span>00000001</span></p>
                <p><strong>Contraseña:</strong> <span>admin123</span></p>
            </div>
            
            <p style="color:#666;font-size:14px;">Usa estas credenciales para ingresar al sistema</p>
            <p class="footer">Solo personal autorizado (Admin / Autoridad)</p>
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
            body {
                font-family: Arial, sans-serif;
                background: #f0f2f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                text-align: center;
                max-width: 450px;
            }
            h1 { color: #1a73e8; }
            .success {
                background: #e8f5e9;
                padding: 20px;
                border-radius: 8px;
                border: 2px solid #4caf50;
                margin: 20px 0;
            }
            .success h3 { color: #2e7d32; margin: 0; }
            .success p { font-size: 18px; }
            .btn {
                display: inline-block;
                padding: 12px 30px;
                background: #1a73e8;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 10px;
            }
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
        <title>Panel Admin</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f0f2f5;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                text-align: center;
                max-width: 450px;
            }
            h1 { color: #1a73e8; }
            .info { background: #e8f0fe; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .info p { margin: 5px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚌 SÍG Transporte</h1>
            <h2 style="color:#666;">Panel de Administración</h2>
            <div class="info">
                <p><strong>✅ Sesión iniciada</strong></p>
                <p>Usuario: 00000001</p>
                <p>Rol: Administrador</p>
            </div>
            <p style="color:#666;font-size:14px;">Bienvenido al sistema</p>
        </div>
    </body>
    </html>
    '''

# Esto es OBLIGATORIO para Render
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
