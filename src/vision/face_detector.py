import cv2
import face_recognition as fcrg
import threading, time

class FaceDetector:

    DEFAULT_CAM = 0

    def __init__(self):
        self.current_face_encoding = None
        self._is_encoding_captured = False
        self._video_capture = None
        self.frame = None
        self._face_locations = None
        self._is_running = False
        self._thread = None
        self._lock = threading.Lock()

    def start_detection(self):
        ''' Inicia a detecção de rostos de maneira não bloqueante.
        '''
        if self._is_running:
            return

        self._is_running = True
        self._thread = threading.Thread(target=self.__face_detection, daemon=True)
        self._thread.start()

    def stop_detection(self):
        ''' Interrompe a detecção, liberando a câmera e encerrando a thread.
        '''
        self._is_running = False

        if self._thread:
            self._thread.join() # Aguarda a thread finalizar
            self._thread = None

        if self._video_capture:
            self._video_capture.release()
            cv2.destroyAllWindows()

    def __face_detection(self):
        ''' Captura a imagem da câmera e caso haja alguem detectável, armazena seu "encoding".
        '''

        # Inicia a captura de vídeo, o número 0 representa a webcam padrão do notebook.
        self._video_capture = cv2.VideoCapture(self.DEFAULT_CAM, cv2.CAP_DSHOW)

        while self._is_running:

            # Captura um único frame (quadro) de vídeo junto a uma flag indicando se ele foi de fato capturado
            ret, frame = self._video_capture.read()
            
            # Se houver algum erro de comunicação com a câmera, encerra
            if not ret or frame is None:
                print("Erro ao acessar a câmera ou ao realizar captura.")
                break

            with self._lock:
                self.frame = frame

            processed_frame = self.__process_frame(frame)
            self._face_locations = fcrg.face_locations(processed_frame)

            if self._face_locations: # Se houver algum rosto sendo detectado
                if not self._is_encoding_captured: # Se o encoding ainda não tiver sido capturado 
                    
                    # Captura o mapeamento do rosto
                    face_encodings = fcrg.face_encodings(processed_frame, self._face_locations)
                    if face_encodings:
                        with self._lock:
                            self.current_face_encoding = face_encodings[0]

                        self._is_encoding_captured = True

            else: # Se não houver nenhum rosto
                self._is_encoding_captured = False

            time.sleep(0.02)

    def __process_frame(self, frame):
        ''' Redimensiona o frame atual para melhor performance e altera o esquema de cores
            para o padrão usado pelo face_recogniton.
        '''

        # Reduzindo o tamanho da imagem para 1/4 para processar mais rápido
        resized_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # A biblioteca face_recognition trabalha com RGB. É necessário converter:
        resized_frame_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

        return resized_frame_rgb