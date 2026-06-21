# SIG Transporte — Backend Flask
## Sistema de Información Geográfica para Transporte Urbano

---

## 🗂️ Estructura del Proyecto

```
sig_transporte_backend/
├── run.py                    ← Punto de entrada
├── seed.py                   ← Datos iniciales (admin, ruta, bus de prueba)
├── camara_parada.py          ← Script OpenCV para la cámara en la parada
├── requirements.txt
├── .env.example              ← Copiar como .env y configurar
├── config/
│   └── config.py             ← Configuración Flask
├── app/
│   ├── __init__.py           ← Factory + extensiones (db, jwt, socketio)
│   ├── models/
│   │   ├── usuario.py        ← Usuario, Rol
│   │   ├── transporte.py     ← Ruta, Parada, Minibus
│   │   ├── operaciones.py    ← Turno, RegistroParada, Alerta, Justificacion
│   │   └── reportes.py       ← Calificacion, Notificacion, TokenDispositivo
│   ├── api/
│   │   ├── auth.py           ← Login, registro pasajero, refresh
│   │   ├── usuarios.py       ← CRUD usuarios (admin)
│   │   ├── rutas.py          ← CRUD rutas y paradas
│   │   ├── minibuses.py      ← CRUD minibuses + generación QR
│   │   ├── registros.py      ← Cámara + escaneo pasajero + mapa
│   │   ├── alertas.py        ← Alertas desvío + justificaciones
│   │   ├── calificaciones.py ← Calificaciones + dashboard
│   │   ├── turnos.py         ← Turnos del chofer
│   │   ├── notificaciones.py ← Push notifications + tokens FCM
│   │   └── reportes.py       ← Generación Excel
│   ├── services/
│   │   ├── notificaciones.py ← FCM push
│   │   ├── reportes.py       ← openpyxl Excel
│   │   ├── qr_service.py     ← Generación imagen QR
│   │   └── calificaciones.py ← Cálculo de puntaje
│   └── utils/
│       ├── helpers.py        ← Haversine, respuestas ok/error
│       └── decorators.py     ← @solo_admin, @solo_chofer, etc.
└── static/
    ├── reports/              ← Excel generados
    └── qr_codes/             ← Imágenes QR de los minibuses
```

---

## ⚙️ Instalación

### 1. Requisitos previos
- Python 3.10+
- PostgreSQL con la extensión PostGIS instalada
- La base de datos `sig_transporte` creada y el SQL ejecutado

### 2. Clonar y configurar
```bash
cd sig_transporte_backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tu contraseña de PostgreSQL y claves JWT
```

### 4. Inicializar la base de datos
```bash
# Primero ejecutar el SQL de la BD:
psql -U postgres -c "CREATE DATABASE sig_transporte;"
psql -U postgres -d sig_transporte -f sig_transporte_database.sql

# Luego cargar datos semilla:
python seed.py
```

### 5. Ejecutar el servidor
```bash
python run.py
```

El servidor arranca en `http://0.0.0.0:5000`

---

## 🔑 Credenciales de prueba (seed.py)

| Rol    | CI       | Password   |
|--------|----------|------------|
| Admin  | 00000001 | admin123   |
| Chofer | 12345678 | chofer123  |

---

## 📡 Endpoints de la API

### Autenticación
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/login` | Login con CI o email |
| POST | `/api/auth/registro-pasajero` | Autoregistro (solo pasajeros) |
| POST | `/api/auth/refresh` | Renovar access token |
| GET  | `/api/auth/perfil` | Perfil del usuario autenticado |
| PUT  | `/api/auth/cambiar-password` | Cambiar contraseña |

### Usuarios (admin)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET  | `/api/usuarios/` | Listar todos |
| POST | `/api/usuarios/` | Crear chofer/autoridad (solo admin) |
| PUT  | `/api/usuarios/<id>` | Actualizar |
| DELETE | `/api/usuarios/<id>` | Desactivar (soft delete) |
| PUT  | `/api/usuarios/<id>/reactivar` | Reactivar |
| GET  | `/api/usuarios/choferes` | Lista rápida de choferes |

### Rutas y Paradas
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET  | `/api/rutas/` | Listar rutas |
| POST | `/api/rutas/` | Crear ruta con paradas (admin) |
| GET  | `/api/rutas/<id>` | Detalle con paradas |
| POST | `/api/rutas/<id>/paradas` | Agregar parada |

### Minibuses
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET  | `/api/minibuses/` | Listar |
| POST | `/api/minibuses/` | Crear + generar QR (admin) |
| POST | `/api/minibuses/<id>/regenerar-qr` | Regenerar imagen QR |
| GET  | `/api/minibuses/por-qr/<codigo>` | **PÚBLICO** — info del bus por QR |

### Registros y Cámara
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/registros/camara` | **PÚBLICO** — cámara detecta QR |
| POST | `/api/registros/pasajero` | **PÚBLICO** — pasajero escanea QR |
| GET  | `/api/registros/mapa` | Estado en tiempo real (mapa) |
| GET  | `/api/registros/` | Listado con filtros |

### Alertas y Justificaciones
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET  | `/api/alertas/` | Listar (chofer ve solo las suyas) |
| POST | `/api/alertas/<id>/justificar` | Chofer envía justificación |
| GET  | `/api/alertas/justificaciones/pendientes` | Admin ve pendientes |
| PUT  | `/api/alertas/justificaciones/<id>/revisar` | Admin acepta/rechaza |
| POST | `/api/alertas/vencidas/procesar` | Procesar alertas vencidas |

### Calificaciones y Dashboard
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET  | `/api/calificaciones/` | Listar por período |
| GET  | `/api/calificaciones/chofer/<id>` | Calificación de un chofer |
| POST | `/api/calificaciones/calcular-todos` | Recalcular todos |
| GET  | `/api/calificaciones/dashboard` | Resumen del dashboard |

### Turnos (chofer)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET  | `/api/turnos/mi-turno` | Turno activo actual |
| POST | `/api/turnos/iniciar` | Iniciar turno |
| PUT  | `/api/turnos/<id>/finalizar` | Finalizar turno |
| GET  | `/api/turnos/mi-historial` | Historial del chofer |

### Reportes Excel
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/reportes/cumplimiento` | Reporte de cumplimiento |
| POST | `/api/reportes/calificaciones` | Reporte de calificaciones |
| POST | `/api/reportes/alertas` | Reporte de alertas |
| GET  | `/api/reportes/descargar/<archivo>` | Descargar Excel |

### Notificaciones
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET  | `/api/notificaciones/` | Mis notificaciones |
| PUT  | `/api/notificaciones/<id>/leer` | Marcar leída |
| PUT  | `/api/notificaciones/leer-todas` | Marcar todas leídas |
| GET  | `/api/notificaciones/no-leidas/count` | Badge contador |
| POST | `/api/notificaciones/token` | Registrar token FCM (Flutter) |

---

## 📷 Cámara en la parada

```bash
# Instalar dependencias de cámara
pip install opencv-python pyzbar

# Ejecutar en la laptop de la parada
python camara_parada.py --parada-id 1 --lat -16.5000 --lon -68.1800 --servidor http://192.168.1.5:5000
```

---

## 🌐 Probar en red local WiFi

1. Ejecutar `python run.py` en la laptop del servidor
2. Todos los celulares y la laptop de la cámara conectados al mismo WiFi
3. Apuntar a `http://192.168.X.X:5000` (la IP de la laptop del servidor)
4. Probar login: `POST /api/auth/login` con `{"identificador":"00000001","password":"admin123"}`

---

## 🧪 Ejemplo de Login con curl

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identificador": "00000001", "password": "admin123"}'
```

Respuesta:
```json
{
  "ok": true,
  "mensaje": "Login exitoso",
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "usuario": { "nombre": "Admin", "rol": "admin", ... }
  }
}
```
