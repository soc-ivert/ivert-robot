import uvicorn
import os
from dotenv import load_dotenv
from src.core.robot import Robot
from src.api.server import create_app

load_dotenv()
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("Variável de ambiente GEMINI_API_KEY não configurada")

def main():

    bot = Robot()
    app = create_app(robot=bot)
    
    print("[MAIN] Iniciando servidor")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
        log_level="warning",
    )

if __name__ == "__main__":
    main()