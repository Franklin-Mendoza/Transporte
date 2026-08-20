import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
import os
import sqlite3
from datetime import datetime
import json

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    
    # Configuración
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///transporte.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # ============================================
    # MODELOS DE BASE DE DATOS
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
        
        def __repr__(self):
            return f'<Usuario {self.ci}>'
    
    class Conductor(db.Model):
        __tablename__ = 'conductor'
        id = db.Column(db.Integer, primary_key=True)
        ci = db.Column(db.String(20), unique=True, nullable=False)
        nombre = db.Column(db.String(100), nullable=False)
        apellido = db.Column(db.String(100), nullable=False)
        licencia = db.Column(db.String(50))
        telefono = db.Column(db.String(20))
        email = db.Column(db.String(100))
        activo = db.Column(db.Boolean, default=True)
        fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    class Vehiculo(db.Model):
        __tablename__ = 'vehiculo'
        id = db.Column(db.Integer, primary_key=True)
        placa = db.Column(db.String(20), unique=True, nullable=False)
        modelo = db.Column(db.String(50))
        marca = db.Column(db.String(50))
        año = db.Column(db.Integer)
        capacidad = db.Column(db.Integer)
        conductor_id = db.Column(db.Integer, db.ForeignKey('conductor.id'))
        activo = db.Column(db.Boolean, default=True)
        fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    class Ruta(db.Model):
        __tablename__ = 'ruta'
        id = db.Column(db.Integer, primary_key=True)
        nombre = db.Column(db.String(100), nullable=False)
        origen = db.Column(db.String(100))
        destino = db.Column(db.String(100))
        distancia = db.Column(db.Float)
        duracion_estimada = db.Column(db.Integer)
        activo = db.Column(db.Boolean, default=True)
        fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ============================================
    # RUTAS TEMPORALES PARA RECUPERAR CONTRASEÑA
    # ============================================
    
    @app.route('/reset-admin')
    def reset_admin():
        try:
            # Verificar si estamos usando SQLite o PostgreSQL
            db_path = 'instance/transporte.db'
            if not os.path.exists(db_path):
                db_path = 'transporte.db'
            
            if os.path.exists(db_path):
                # Usar SQLite directo
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Ver tablas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tablas = cursor.fetchall()
                
                # Buscar tabla de usuarios
                tabla_usuario = None
                for tabla in tablas:
                    nombre = tabla[0]
                    if nombre in ['usuario', 'admin', 'usuarios', 'user']:
                        tabla_usuario = nombre
                        break
                
                if not tabla_usuario:
                    return f"❌ No se encontró tabla de usuarios. Tablas disponibles: {[t[0] for t in tablas]}"
                
                # Ver columnas
                cursor.execute(f"PRAGMA table_info({tabla_usuario})")
                columnas = [col[1] for col in cursor.fetchall()]
                
                if 'ci' in columnas and 'password' in columnas:
                    # Actualizar o crear usuario
                    cursor.execute(f"UPDATE {tabla_usuario} SET password = 'admin123' WHERE ci = '00000001'")
                    if cursor.rowcount == 0:
                        if 'rol' in columnas:
                            cursor.execute(f"INSERT INTO {tabla_usuario} (ci, password, rol) VALUES ('00000001', 'admin123', 'admin')")
                        else:
                            cursor.execute(f"INSERT INTO {tabla_usuario} (ci, password) VALUES ('00000001', 'admin123')")
                    conn.commit()
                    conn.close()
                    return f"✅ CONTRASEÑA ACTUALIZADA en tabla '{tabla_usuario}' a 'admin123' para CI=00000001"
                else:
                    return f"❌ La tabla {tabla_usuario} tiene columnas: {columnas}"
            else:
                # Usar SQLAlchemy
                with app.app_context():
                    admin = Usuario.query.filter_by(ci='00000001').first()
                    if admin:
                        admin.password = bcrypt.generate_password_hash('admin123').decode('utf-8')
                        db.session.commit()
                        return "✅ Contraseña actualizada a 'admin123' usando SQLAlchemy"
                    else:
                        nuevo_admin = Usuario(
                            ci='00000001',
                            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                            rol='admin',
                            nombre='Administrador',
                            apellido='Sistema'
                        )
                        db.session.add(nuevo_admin)
                        db.session.commit()
                        return "✅ Usuario admin creado con contraseña 'admin123'"
                    
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    @app.route('/ver-tablas')
    def ver_tablas():
        try:
            db_path = 'instance/transporte.db'
            if not os.path.exists(db_path):
                db_path = 'transporte.db'
            
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tablas = cursor.fetchall()
                
                html = "<h2>📊 Base de datos SQLite</h2>"
                html += f"<p><b>Archivo:</b> {db_path}</p>"
                html += "<h3>Tablas encontradas:</h3><ul>"
                
                for t in tablas:
                    nombre = t[0]
                    cursor.execute(f"PRAGMA table_info({nombre})")
                    columnas = [f"{col[1]} ({col[2]})" for col in cursor.fetchall()]
                    cursor.execute(f"SELECT COUNT(*) FROM {nombre}")
                    count = cursor.fetchone()[0]
                    html += f"<li><b>{nombre}</b> → {count} registros<br>Columnas: {', '.join(columnas)}</li>"
                
                html += "</ul>"
                
                # Mostrar usuarios si existe
                for t in tablas:
                    if t[0] in ['usuario', 'admin', 'usuarios', 'user']:
                        cursor.execute(f"SELECT * FROM {t[0]} LIMIT 10")
                        datos = cursor.fetchall()
                        if datos:
                            html += f"<h3>Usuarios en '{t[0]}':</h3><ul>"
                            for d in datos:
                                html += f"<li>{d}</li>"
                            html += "</ul>"
                
                conn.close()
                return html
            else:
                return "❌ No se encontró archivo SQLite. Usando PostgreSQL con SQLAlchemy."
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    @app.route('/crear-admin-directo')
    def crear_admin_directo():
        try:
            with app.app_context():
                # Verificar si existe
                admin = Usuario.query.filter_by(ci='00000001').first()
                if admin:
                    admin.password = bcrypt.generate_password_hash('admin123').decode('utf-8')
                    db.session.commit()
                    return "✅ Admin actualizado: CI=00000001, Password=admin123"
                else:
                    nuevo = Usuario(
                        ci='00000001',
                        password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                        rol='admin',
                        nombre='Administrador',
                        apellido='Sistema'
                    )
                    db.session.add(nuevo)
                    db.session.commit()
                    return "✅ Admin creado: CI=00000001, Password=admin123"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    # ============================================
    # FIN RUTAS TEMPORALES
    # ============================================
    
    # ============================================
    # RUTAS PRINCIPALES
    # ============================================
    
    @app.route('/')
    def index():
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>SÍG Transporte</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f0f2f5; }
                .container { max-width: 400px; margin: 100px auto; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #1a73e8; text-align: center; }
                .info { background: #e8f0fe; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .info h3 { margin: 0; color: #1a73e8; }
                .links { text-align: center; margin-top: 20px; }
                .links a { display: inline-block; margin: 5px 10px; color: #1a73e8; text-decoration: none; }
                .links a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚌 SÍG Transporte</h1>
                <h2 style="text-align:center;color:#666;">Panel de Administración</h2>
                
                <div class="info">
                    <h3>🔐 Credenciales de acceso:</h3>
                    <p><strong>Usuario:</strong> 00000001</p>
                    <p><strong>Contraseña:</strong> admin123</p>
                </div>
                
                <div class="links">
                    <a href="/reset-admin">🔄 Restablecer contraseña</a><br>
                    <a href="/ver-tablas">📊 Ver estructura DB</a><br>
                    <a href="/crear-admin-directo">➕ Crear admin directo</a>
                </div>
                
                <p style="text-align:center;margin-top:30px;color:#999;font-size:12px;">
                    Solo personal autorizado (Admin / Autoridad)<br>
                    Acceso de choferes y pasajeros desde app móvil
                </p>
            </div>
        </body>
        </html>
        '''
    
    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        ci = data.get('ci')
        password = data.get('password')
        
        if not ci or not password:
            return jsonify({'error': 'CI y contraseña requeridos'}), 400
        
        with app.app_context():
            usuario = Usuario.query.filter_by(ci=ci).first()
            if usuario and bcrypt.check_password_hash(usuario.password, password):
                session['user_id'] = usuario.id
                session['user_ci'] = usuario.ci
                session['user_rol'] = usuario.rol
                return jsonify({
                    'success': True,
                    'message': 'Login exitoso',
                    'user': {
                        'ci': usuario.ci,
                        'nombre': usuario.nombre,
                        'rol': usuario.rol
                    }
                })
        
        return jsonify({'error': 'Credenciales incorrectas'}), 401
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect('/')
    
    # Crear tablas si no existen
    with app.app_context():
        db.create_all()
        
        # Crear usuario admin por defecto si no existe
        admin = Usuario.query.filter_by(ci='00000001').first()
        if not admin:
            admin = Usuario(
                ci='00000001',
                password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
                rol='admin',
                nombre='Administrador',
                apellido='Sistema'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuario admin creado por defecto: CI=00000001, Password=admin123")
    
    return app

# Para ejecutar directamente
if __name__ == '__main__':
    app = create_app()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    print(f"""
╔══════════════════════════════════════════╗
║      SIG TRANSPORTE — Backend Flask      ║
║  Servidor: http://{host}:{port}           ║
║  Modo:     {'DEBUG' if debug else 'PRODUCCIÓN'}                       ║
╚══════════════════════════════════════════╝
    """)
    
    socketio.run(app, host=host, port=port, debug=debug)
