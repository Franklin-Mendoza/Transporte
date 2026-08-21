import eventlet
eventlet.monkey_patch()

from app import create_app, socketio

app = create_app()

if __name__ == "__main__":
    import os
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
