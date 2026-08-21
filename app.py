import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================

app = Flask(__name__)
app.secret_key = 'clave-secreta-para-desarrollo'

# Configurar base de datos (usa SQLite para simplificar)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'transporte.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ============================================
# INICIALIZAR EXTENSIONES
# ============================================

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ============================================
# MODELOS
# ============================================

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    ci = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(50), nullable=False, default='usuario')
    nombre = db.Column(db.String(100))
    apellido = db.Column(db.String(100))
    email = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================
# CREAR TABLAS Y USUARIO ADMIN
# ============================================

with app.app_context():
    db.create_all()
    
    # Crear usuario admin si no existe
    admin = Usuario.query.filter_by(ci='00000001').first()
    if not admin:
        admin = Usuario(
            ci='00000001',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            rol='admin',
            nombre='Administrador',
            apellido='Sistema',
            email='admin@sigtransport.com',
            activo=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuario admin creado: CI=00000001, Password=admin123")
    else:
        # Asegurar que la contraseña sea admin123
        admin.password = bcrypt.generate_password_hash('admin123').decode('utf-8')
        db.session.commit()
        print("✅ Contraseña de admin actualizada: CI=00000001, Password=admin123")

# ============================================
# RUTAS
# ============================================

@app.route('/')
def index():
    return render_template_string('''
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
            .error { color: red; margin: 10px 0; }
            .info { background: #e8f0fe; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .info p { margin: 5px 0; }
            .footer { color: #999; font-size: 12px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚌 SÍG Transporte</h1>
            <h2 style="color:#666;font-size:18px;">Panel de Administración</h2>
            
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    <div class="error">{{ messages[0] }}</div>
                {% endif %}
            {% endwith %}
            
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
    ''')

@app.route('/login', methods=['POST'])
def login():
    ci = request.form.get('ci')
    password = request.form.get('password')
    
    if not ci or not password:
        flash('CI y contraseña son requeridos')
        return redirect(url_for('index'))
    
    usuario = Usuario.query.filter_by(ci=ci).first()
    
    if usuario and bcrypt.check_password_hash(usuario.password, password):
        session['user_id'] = usuario.id
        session['user_ci'] = usuario.ci
        session['user_rol'] = usuario.rol
        session['user_nombre'] = usuario.nombre or usuario.ci
        return redirect(url_for('dashboard'))
    else:
        flash('Credenciales incorrectas. Usuario: 00000001 - Contraseña: admin123')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero')
        return redirect(url_for('index'))
    
    return render_template_string('''
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
                <span>👤 {{ session.user_nombre }} ({{ session.user_ci }})</span>
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
                    <div class="number">{{ usuarios_count }}</div>
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
    ''', usuarios_count=Usuario.query.count())

@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente')
    return redirect(url_for('index'))

@app.route('/usuarios')
def usuarios():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero')
        return redirect(url_for('index'))
    
    usuarios = Usuario.query.all()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Usuarios - SÍG Transporte</title>
        <style>
            body { font-family: Arial; margin: 0; padding: 0; background: #f0f2f5; }
            .header { background: #1a73e8; color: white; padding: 20px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { margin: 0; }
            .header a { color: white; text-decoration: none; padding: 8px 16px; background: rgba(255,255,255,0.2); border-radius: 5px; }
            .header a:hover { background: rgba(255,255,255,0.3); }
            .container { max-width: 1200px; margin: 20px auto; padding: 20px; }
            .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .card h2 { margin-top: 0; color: #1a73e8; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #e8f0fe; }
            .back { margin-top: 20px; display: inline-block; color: #1a73e8; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚌 SÍG Transporte</h1>
            <div>
                <span>👤 ''' + session.get('user_nombre', session.get('user_ci')) + '''</span>
                <a href="/logout">Cerrar sesión</a>
            </div>
        </div>
        
        <div class="container">
            <div class="card">
                <h2>👥 Gestión de Usuarios</h2>
                <table>
                    <tr>
                        <th>CI</th>
                        <th>Nombre</th>
                        <th>Rol</th>
                        <th>Estado</th>
                    </tr>
    '''
    
    for u in usuarios:
        html += f'''
                    <tr>
                        <td>{u.ci}</td>
                        <td>{u.nombre or ''} {u.apellido or ''}</td>
                        <td>{u.rol}</td>
                        <td>{"✅ Activo" if u.activo else "❌ Inactivo"}</td>
                    </tr>
        '''
    
    html += '''
                </table>
                <a href="/dashboard" class="back">← Volver al Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html

@app.route('/conductores')
def conductores():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero')
        return redirect(url_for('index'))
    return '<h1>🚧 Conductores - En construcción</h1><a href="/dashboard">Volver</a>'

@app.route('/vehiculos')
def vehiculos():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero')
        return redirect(url_for('index'))
    return '<h1>🚧 Vehículos - En construcción</h1><a href="/dashboard">Volver</a>'

@app.route('/rutas')
def rutas():
    if 'user_id' not in session:
        flash('Por favor inicia sesión primero')
        return redirect(url_for('index'))
    return '<h1>🚧 Rutas - En construcción</h1><a href="/dashboard">Volver</a>'

# ============================================
# EJECUTAR
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
