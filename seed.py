"""
Script para inicializar la base de datos con datos semilla.
Ejecutar UNA SOLA VEZ después de crear la BD:

    python seed.py

"""
from app import create_app, db, bcrypt
from app.models import Rol, Usuario, Ruta, Parada, Minibus


def seed():
    app = create_app()
    with app.app_context():
        print("🌱 Inicializando base de datos...")

        # Crear tablas
        db.create_all()

        # ── Roles ────────────────────────────────────
        roles_data = [
            ("admin",      "Administrador del sistema. Acceso total."),
            ("autoridad",  "Supervisión en tiempo real. Solo lectura y reportes."),
            ("chofer",     "Operador del minibús. Ve su ruta y sus alertas."),
            ("pasajero",   "Usuario final. Escanea QR del bus. Puede autoregistrarse."),
        ]
        for nombre, desc in roles_data:
            if not Rol.query.filter_by(nombre=nombre).first():
                db.session.add(Rol(nombre=nombre, descripcion=desc))
        db.session.commit()
        print("  ✓ Roles creados")

        # ── Admin principal ──────────────────────────
        rol_admin = Rol.query.filter_by(nombre="admin").first()
        if not Usuario.query.filter_by(numero_ci="00000001").first():
            admin = Usuario(
                nombre="Admin",
                apellido="Sistema",
                numero_ci="00000001",
                email="admin@sig.bo",
                password_hash=bcrypt.generate_password_hash("admin123").decode("utf-8"),
                rol_id=rol_admin.id,
                puede_autoregistrarse=False,
            )
            db.session.add(admin)
            db.session.commit()
            print("  ✓ Admin creado  →  CI: 00000001  |  Password: admin123")
        else:
            print("  ✓ Admin ya existe")

        # ── Chofer de prueba ─────────────────────────
        rol_chofer = Rol.query.filter_by(nombre="chofer").first()
        admin_obj = Usuario.query.filter_by(numero_ci="00000001").first()

        if not Usuario.query.filter_by(numero_ci="12345678").first():
            chofer = Usuario(
                nombre="Carlos",
                apellido="Mamani",
                numero_ci="12345678",
                email="chofer1@sig.bo",
                password_hash=bcrypt.generate_password_hash("chofer123").decode("utf-8"),
                rol_id=rol_chofer.id,
                puede_autoregistrarse=False,
                creado_por=admin_obj.id,
            )
            db.session.add(chofer)
            db.session.commit()
            print("  ✓ Chofer de prueba creado  →  CI: 12345678  |  Password: chofer123")

        # ── Ruta de prueba ───────────────────────────
        if not Ruta.query.filter_by(codigo="R01").first():
            ruta = Ruta(
                codigo="R01",
                nombre="Ruta 1 — El Alto Centro",
                descripcion="Ruta de prueba para el sistema SIG",
                creado_por=admin_obj.id,
            )
            db.session.add(ruta)
            db.session.flush()

            # Paradas de ejemplo (coordenadas La Paz / El Alto)
            paradas_ejemplo = [
                ("Terminal El Alto",     -16.5000, -68.1800, 1),
                ("Plaza Ballivián",      -16.5050, -68.1750, 2),
                ("Mercado 16 de Julio",  -16.5100, -68.1700, 3),
                ("Zona Villa Dolores",   -16.5150, -68.1650, 4),
                ("Terminal TRUFIS",      -16.5200, -68.1600, 5),
            ]
            for nombre, lat, lon, orden in paradas_ejemplo:
                db.session.add(Parada(
                    ruta_id=ruta.id,
                    nombre=nombre,
                    orden=orden,
                    latitud=lat,
                    longitud=lon,
                    radio_metros=80,
                ))
            db.session.commit()
            print(f"  ✓ Ruta R01 creada con {len(paradas_ejemplo)} paradas")

        # ── Minibús de prueba ────────────────────────
        ruta_obj = Ruta.query.filter_by(codigo="R01").first()
        chofer_obj = Usuario.query.filter_by(numero_ci="12345678").first()

        if not Minibus.query.filter_by(placa="2345-ABC").first():
            bus = Minibus(
                placa="2345-ABC",
                codigo_qr="BUS-2345-ABC-SIG2026",
                ruta_id=ruta_obj.id if ruta_obj else None,
                chofer_id=chofer_obj.id if chofer_obj else None,
                modelo="Toyota Hiace",
                color="Blanco",
                capacidad=12,
            )
            db.session.add(bus)
            db.session.commit()
            print("  ✓ Minibús de prueba creado  →  Placa: 2345-ABC  |  QR: BUS-2345-ABC-SIG2026")

        print("""
╔══════════════════════════════════════════╗
║     ✅ Base de datos lista               ║
╠══════════════════════════════════════════╣
║  Admin:   CI 00000001  / admin123        ║
║  Chofer:  CI 12345678  / chofer123       ║
║  QR bus:  BUS-2345-ABC-SIG2026           ║
╚══════════════════════════════════════════╝
        """)


if __name__ == "__main__":
    seed()
