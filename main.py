import uvicorn

from src.core.robot import Robot
from src.api.server import create_app

def main():

    bot = Robot()
    bot.start()

    app = create_app(robot=bot)
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