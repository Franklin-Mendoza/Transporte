import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_cambiar_en_produccion")
    DEBUG = False
    TESTING = False

    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/sig_transporte"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt_dev_secret_cambiar")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 2592000))
    )

    # Carpetas de archivos
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "./static/uploads")
    REPORTS_FOLDER = os.getenv("REPORTS_FOLDER", "./static/reports")
    QR_FOLDER = os.getenv("QR_FOLDER", "./static/qr_codes")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB máximo por upload

    # Firebase Cloud Messaging
    FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")

    # Geo
    RADIO_TOLERANCIA_METROS = int(os.getenv("RADIO_TOLERANCIA_METROS", 100))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
