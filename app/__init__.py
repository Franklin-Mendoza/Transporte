import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
socketio = SocketIO()


def create_app(config_name=None):
    app = Flask(__name__, static_folder="../static")

    # Cargar configuración
    from config import config_map
    env = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_map.get(env, config_map["default"]))

    # Crear carpetas necesarias
    for folder_key in ["UPLOAD_FOLDER", "REPORTS_FOLDER", "QR_FOLDER"]:
        folder = app.config.get(folder_key, "")
        if folder:
            os.makedirs(folder, exist_ok=True)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode="eventlet")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Registrar blueprints de la API
    from app.api import registrar_blueprints
    registrar_blueprints(app)

    # Registrar blueprint de vistas web (panel admin/autoridad)
    from app.views import vistas_bp
    app.register_blueprint(vistas_bp)

    # Importar todos los modelos para que Flask-Migrate los detecte
    with app.app_context():
        from app.models import (
            Usuario, Rol, Ruta, Parada, Minibus,
            Turno, RegistroParada, EscaneosPasajero,
            AlertaDesvio, Justificacion,
            Calificacion, Notificacion, ReporteGenerado, TokenDispositivo
        )

    # Ruta de salud de la API (separada del panel web)
    @app.route("/health")
    def health():
        return {"ok": True, "sistema": "SIG Transporte", "version": "1.0.0"}

    # Eventos SocketIO para el mapa en tiempo real
    @socketio.on("connect")
    def on_connect():
        print("Cliente conectado al mapa en tiempo real")

    @socketio.on("disconnect")
    def on_disconnect():
        print("Cliente desconectado")

    return app
