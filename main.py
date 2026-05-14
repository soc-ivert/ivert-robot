import uvicorn
from src.api.server import create_app
from src.vision.face_detector import FaceDetector

DB_PATH = "data/bot.db"

def main():
    
    detector = FaceDetector()
    detector.start_detection()

    app = create_app(detector=detector)

    uvicorn.run(app, host="0.0.0.0", port=8500, ssl_keyfile="key.pem", ssl_certfile="cert.pem")

if __name__ == "__main__":
    main()