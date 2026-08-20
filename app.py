import os
from flask import Flask

app = Flask(__name__)

# Ruta principal
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SÍG Transporte</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 0; background: #f0f2f5; }
            .container { max-width: 500px; margin: 100px auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
            h1 { color: #1a73e8; }
            .info { background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .info h3 { color: #2e7d32; margin: 0; }
            .btn { display: inline-block; padding: 12px 30px; background: #1a73e8; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; }
            .btn:hover { background: #1557b0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚌 SÍG Transporte</h1>
            <h2>🔐 Acceso Restablecido</h2>
            <div class="info">
                <h3>✅ Contraseña restablecida</h3>
                <p><strong>Usuario:</strong> 00000001</p>
                <p><strong>Contraseña:</strong> admin123</p>
            </div>
            <a href="/login" class="btn">Ir al Login</a>
            <p style="color:#666;font-size:12px;margin-top:20px;">Solo personal autorizado (Admin / Autoridad)</p>
        </div>
    </body>
    </html>
    '''

@app.route('/login')
def login():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SÍG Transporte - Login</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 0; background: #f0f2f5; }
            .container { max-width: 400px; margin: 100px auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #1a73e8; text-align: center; }
            .info { background: #e8f0fe; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .info p { margin: 5px 0; }
            input { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; }
            .btn { width: 100%; padding: 12px; background: #1a73e8; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; }
            .btn:hover { background: #1557b0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚌 SÍG Transporte</h1>
            <h2 style="text-align:center;color:#666;">Panel de Administración</h2>
            <div class="info">
                <p><strong>Usuario:</strong> 00000001</p>
                <p><strong>Contraseña:</strong> admin123</p>
            </div>
            <form action="/login" method="POST">
                <input type="text" placeholder="Número de CI" value="00000001">
                <input type="password" placeholder="Contraseña" value="admin123">
                <button class="btn" type="submit">Ingresar</button>
            </form>
            <p style="text-align:center;margin-top:20px;color:#999;font-size:12px;">
                Solo personal autorizado (Admin / Autoridad)
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/reset')
def reset():
    return "✅ Contraseña restablecida: USUARIO=00000001, PASSWORD=admin123"

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
