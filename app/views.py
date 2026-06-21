from flask import Blueprint, render_template, session

vistas_bp = Blueprint("vistas", __name__)


@vistas_bp.route("/")
def index():
    return render_template("auth/login.html")


@vistas_bp.route("/login")
def login_page():
    return render_template("auth/login.html")


@vistas_bp.route("/dashboard")
def dashboard_page():
    # El rol real se valida en JS contra localStorage (protegerPagina).
    # Aquí solo pasamos un valor por defecto para que el sidebar se renderice;
    # el JS ajusta la visibilidad real según el usuario autenticado.
    return render_template("admin/dashboard.html", rol="admin")


@vistas_bp.route("/mapa")
def mapa_page():
    return render_template("admin/mapa.html", rol="admin")


@vistas_bp.route("/escaneos")
def escaneos_page():
    return render_template("admin/escaneos.html", rol="admin")


@vistas_bp.route("/camaras")
def camaras_page():
    return render_template("admin/camaras.html", rol="admin")


@vistas_bp.route("/operacion-camaras")
def operacion_camaras_page():
    return render_template("admin/operacion_camaras.html", rol="admin")


@vistas_bp.route("/usuarios")
def usuarios_page():
    return render_template("admin/usuarios.html", rol="admin")


@vistas_bp.route("/rutas")
def rutas_page():
    return render_template("admin/rutas.html", rol="admin")


@vistas_bp.route("/minibuses")
def minibuses_page():
    return render_template("admin/minibuses.html", rol="admin")


@vistas_bp.route("/alertas")
def alertas_page():
    return render_template("admin/alertas.html", rol="admin")


@vistas_bp.route("/calificaciones")
def calificaciones_page():
    return render_template("admin/calificaciones.html", rol="admin")


@vistas_bp.route("/reportes")
def reportes_page():
    return render_template("admin/reportes.html", rol="admin")
