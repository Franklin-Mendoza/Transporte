"""
camara_parada.py
────────────────
Script Python que corre en la laptop/Raspberry Pi de la PARADA.
Lee el QR del minibús con la cámara y notifica al servidor Flask.

Uso:
    python camara_parada.py --parada-id 1 --lat -16.5000 --lon -68.1800 --servidor http://192.168.1.5:5000

Requisitos:
    pip install opencv-python pyzbar requests
"""

import cv2
import requests
import argparse
import time
from pyzbar import pyzbar
from datetime import datetime


def leer_qr_camara(parada_id, latitud, longitud, servidor_url, camara_idx=0):
    cap = cv2.VideoCapture(camara_idx)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara")
        return

    print(f"""
╔══════════════════════════════════════════╗
║    CÁMARA EN PARADA — SIG Transporte     ║
║  Parada ID : {parada_id:<27} ║
║  Servidor  : {servidor_url:<27} ║
║  Coords    : {latitud}, {longitud}
║  Presiona Q para salir                   ║
╚══════════════════════════════════════════╝
    """)

    qrs_registrados = {}  # codigo_qr → timestamp del último registro
    COOLDOWN_SEGUNDOS = 30  # No registrar el mismo QR en menos de 30 seg

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️  Error leyendo frame de la cámara")
            continue

        qrs = pyzbar.decode(frame)
        for qr in qrs:
            codigo = qr.data.decode("utf-8")
            ahora = time.time()

            # Dibujar rectángulo sobre el QR detectado
            pts = qr.polygon
            if len(pts) == 4:
                import numpy as np
                pts = np.array(pts, dtype=np.int32)
                cv2.polylines(frame, [pts], True, (0, 255, 0), 3)
            cv2.putText(frame, codigo, (qr.rect.left, qr.rect.top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Cooldown para evitar registros duplicados rápidos
            ultimo = qrs_registrados.get(codigo, 0)
            if ahora - ultimo < COOLDOWN_SEGUNDOS:
                restante = int(COOLDOWN_SEGUNDOS - (ahora - ultimo))
                print(f"⏳ QR {codigo} ya registrado hace poco. Espera {restante}s")
                continue

            # Enviar al servidor Flask
            print(f"📡 QR detectado: {codigo} — enviando al servidor...")
            try:
                resp = requests.post(
                    f"{servidor_url}/api/registros/camara",
                    json={
                        "codigo_qr": codigo,
                        "parada_id": parada_id,
                        "latitud_camara": latitud,
                        "longitud_camara": longitud,
                    },
                    timeout=5,
                )
                data = resp.json()
                if data.get("ok"):
                    hora = datetime.now().strftime("%H:%M:%S")
                    print(f"  ✓ [{hora}] Registrado: {data['data']['parada']} — En ruta: {data['data']['en_ruta']}")
                    qrs_registrados[codigo] = ahora
                else:
                    print(f"  ⚠️  Servidor respondió: {data.get('mensaje')}")
            except requests.exceptions.ConnectionError:
                print(f"  ❌ No se pudo conectar al servidor: {servidor_url}")
            except Exception as e:
                print(f"  ❌ Error: {e}")

        # Mostrar vista de la cámara con overlay
        cv2.imshow("SIG Transporte — Cámara Parada", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("👋 Cerrando cámara...")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cámara de parada SIG Transporte")
    parser.add_argument("--parada-id", type=int, required=True, help="ID de la parada donde está la cámara")
    parser.add_argument("--lat", type=float, required=True, help="Latitud de la cámara/parada")
    parser.add_argument("--lon", type=float, required=True, help="Longitud de la cámara/parada")
    parser.add_argument("--servidor", type=str, default="http://localhost:5000", help="URL del servidor Flask")
    parser.add_argument("--camara", type=int, default=0, help="Índice de la cámara (0 = default)")
    args = parser.parse_args()

    leer_qr_camara(
        parada_id=args.parada_id,
        latitud=args.lat,
        longitud=args.lon,
        servidor_url=args.servidor,
        camara_idx=args.camara,
    )
