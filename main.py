import uvicorn
import os
from dotenv import load_dotenv
from src.core.robot import Robot
from src.api.server import create_app

load_dotenv()

def main():

    env_vars = ["GEMINI_API_KEY", "TABLET_ACCESS_TOKEN"]

    for env_var in env_vars:
        if not os.getenv(env_var):
            raise ValueError(f"Variável de ambiente {env_var} não configurada")

    for cert_file in ["key.pem", "cert.pem"]:
        if not os.path.exists(cert_file):
            raise FileNotFoundError(f"Certificado não encontrado: {cert_file}")

    bot = Robot()
    app = create_app(robot=bot)
    port = int(os.getenv("PORT", 8484))
    host = os.getenv("HOST", "0.0.0.0")

    print("[MAIN] Iniciando servidor")
    uvicorn.run(
        app,
        host=host,
        port=port,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
        log_level="warning",
        ws_ping_interval=None,
        ws_ping_timeout=None,
    )

if __name__ == "__main__":
    main()