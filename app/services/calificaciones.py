from datetime import datetime
from app import db
from app.models import Calificacion, RegistroParada, AlertaDesvio, Justificacion


def calcular_calificacion_chofer(chofer_id, periodo=None):
    """
    Calcula y guarda (o actualiza) la calificación de un chofer para un período.
    periodo: string 'YYYY-MM', por defecto el mes actual.
    """
    if not periodo:
        periodo = datetime.utcnow().strftime("%Y-%m")

    # Total de registros en el período
    total = RegistroParada.query.filter(
        RegistroParada.chofer_id == chofer_id,
        db.func.to_char(RegistroParada.registrado_en, "YYYY-MM") == periodo
    ).count()

    # Paradas OK (en ruta)
    paradas_ok = RegistroParada.query.filter(
        RegistroParada.chofer_id == chofer_id,
        RegistroParada.en_ruta == True,
        db.func.to_char(RegistroParada.registrado_en, "YYYY-MM") == periodo
    ).count()

    # Alertas generadas en el período
    alertas = AlertaDesvio.query.filter(
        AlertaDesvio.chofer_id == chofer_id,
        db.func.to_char(AlertaDesvio.generada_en, "YYYY-MM") == periodo
    ).count()

    # Justificaciones aceptadas
    justif_aceptadas = db.session.query(Justificacion).join(
        AlertaDesvio, Justificacion.alerta_id == AlertaDesvio.id
    ).filter(
        Justificacion.chofer_id == chofer_id,
        Justificacion.estado == "aceptada",
        db.func.to_char(AlertaDesvio.generada_en, "YYYY-MM") == periodo
    ).count()

    faltas_acumuladas = max(0, alertas - justif_aceptadas)

    # Buscar o crear la calificación
    cal = Calificacion.query.filter_by(chofer_id=chofer_id, periodo=periodo).first()
    if not cal:
        cal = Calificacion(chofer_id=chofer_id, periodo=periodo)
        db.session.add(cal)

    cal.total_paradas = total
    cal.paradas_ok = paradas_ok
    cal.alertas_generadas = alertas
    cal.faltas_justificadas = justif_aceptadas
    cal.faltas_acumuladas = faltas_acumuladas
    cal.fecha_calculo = datetime.utcnow().date()
    cal.calcular_y_guardar()

    db.session.commit()
    return cal
