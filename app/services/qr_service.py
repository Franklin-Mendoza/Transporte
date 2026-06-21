import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
from flask import current_app


def generar_qr_minibus(codigo_qr, placa, ruta_nombre=""):
    """
    Genera una imagen QR para un minibús con información visual.
    Retorna la ruta del archivo generado.
    """
    carpeta = current_app.config.get("QR_FOLDER", "./static/qr_codes")
    os.makedirs(carpeta, exist_ok=True)

    nombre_archivo = f"qr_{placa.replace('-', '_')}.png"
    ruta_archivo = os.path.join(carpeta, nombre_archivo)

    # Crear QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    # El contenido del QR es el código único del minibús
    qr.add_data(codigo_qr)
    qr.make(fit=True)

    # Imagen del QR en azul oscuro y blanco
    img_qr = qr.make_image(fill_color="#1A3A5C", back_color="white")

    # Agregar texto debajo
    ancho_qr = img_qr.size[0]
    alto_extra = 80
    img_final = Image.new("RGB", (ancho_qr, img_qr.size[1] + alto_extra), "white")
    img_final.paste(img_qr, (0, 0))

    draw = ImageDraw.Draw(img_final)

    # Texto de placa y ruta
    try:
        font_grande = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_chico = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except Exception:
        font_grande = ImageFont.load_default()
        font_chico = font_grande

    y_texto = img_qr.size[1] + 8
    draw.text((ancho_qr // 2, y_texto), f"PLACA: {placa}", fill="#1A3A5C",
              font=font_grande, anchor="mt")
    if ruta_nombre:
        draw.text((ancho_qr // 2, y_texto + 28), ruta_nombre, fill="#666666",
                  font=font_chico, anchor="mt")
    draw.text((ancho_qr // 2, y_texto + 52), "Escanea para ver el estado del minibús",
              fill="#999999", font=font_chico, anchor="mt")

    img_final.save(ruta_archivo, "PNG", dpi=(300, 300))

    url_relativa = f"/static/qr_codes/{nombre_archivo}"
    return ruta_archivo, url_relativa
