import uvicorn
from src.api.server import create_app

DB_PATH = "data/bot.db"

def main():

    app = create_app(robot=None)
    uvicorn.run(app, host="0.0.0.0", port=8500, ssl_keyfile="key.pem", ssl_certfile="cert.pem")

if __name__ == "__main__":
    main()