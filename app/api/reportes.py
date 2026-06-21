from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.utils import ok, error, admin_o_autoridad
from app.services.reportes import (
    generar_reporte_cumplimiento,
    generar_reporte_calificaciones,
    generar_reporte_alertas,
)

reportes_bp = Blueprint("reportes", __name__, url_prefix="/api/reportes")


@reportes_bp.route("/cumplimiento", methods=["POST"])
@jwt_required()
@admin_o_autoridad
def reporte_cumplimiento():
    """Genera reporte Excel de cumplimiento de rutas."""
    data = request.get_json() or {}
    admin_id = get_jwt_identity()

    desde = data.get("desde")
    hasta = data.get("hasta")
    ruta_id = data.get("ruta_id")

    try:
        ruta_archivo, url = generar_reporte_cumplimiento(
            desde=desde, hasta=hasta, ruta_id=ruta_id, generado_por_id=admin_id
        )
        return ok({"url": url, "archivo": ruta_archivo.split("/")[-1]},
                  "Reporte generado correctamente")
    except Exception as e:
        return error(f"Error generando reporte: {str(e)}", 500)


@reportes_bp.route("/calificaciones", methods=["POST"])
@jwt_required()
@admin_o_autoridad
def reporte_calificaciones():
    """Genera reporte Excel de calificaciones por período."""
    data = request.get_json() or {}
    admin_id = get_jwt_identity()
    periodo = data.get("periodo", datetime.utcnow().strftime("%Y-%m"))

    try:
        ruta_archivo, url = generar_reporte_calificaciones(
            periodo=periodo, generado_por_id=admin_id
        )
        return ok({"url": url, "archivo": ruta_archivo.split("/")[-1]},
                  "Reporte generado correctamente")
    except Exception as e:
        return error(f"Error generando reporte: {str(e)}", 500)


@reportes_bp.route("/alertas", methods=["POST"])
@jwt_required()
@admin_o_autoridad
def reporte_alertas():
    """Genera reporte Excel de alertas de desvío."""
    data = request.get_json() or {}
    admin_id = get_jwt_identity()

    try:
        ruta_archivo, url = generar_reporte_alertas(
            desde=data.get("desde"),
            hasta=data.get("hasta"),
            chofer_id=data.get("chofer_id"),
            generado_por_id=admin_id,
        )
        return ok({"url": url, "archivo": ruta_archivo.split("/")[-1]},
                  "Reporte generado correctamente")
    except Exception as e:
        return error(f"Error generando reporte: {str(e)}", 500)


@reportes_bp.route("/descargar/<string:nombre_archivo>", methods=["GET"])
@jwt_required()
@admin_o_autoridad
def descargar_reporte(nombre_archivo):
    """Descarga directa de un archivo Excel generado."""
    import os
    from flask import current_app
    carpeta = current_app.config.get("REPORTS_FOLDER", "./static/reports")
    ruta = os.path.join(carpeta, nombre_archivo)
    if not os.path.exists(ruta):
        return error("Archivo no encontrado", 404)
    return send_file(ruta, as_attachment=True, download_name=nombre_archivo)
