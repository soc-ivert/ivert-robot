import cv2
import face_recognition as fcrg
import threading, time

class FaceDetector:
    """ Gerencia a detecção e extração de características faciais em segundo plano.

    Esta classe executa um loop assíncrono em uma thread separada para capturar e 
    processar frames de vídeo. Permite tanto a captura direta de dispositivos locais 
    quanto a injeção externa de frames (Stream/WebSocket).

    Attributes:
        current_face_encoding (np.ndarray | None): Vetor de dimensões do rosto detectado.
        source (int | str | None): Fonte do vídeo (ID numérico da webcam ou caminho do arquivo).
        frame (numpy.ndarray | None): O frame atual retido para processamento.
        DEFAULT_SOURCE (None): Constante que define o comportamento padrão sem câmera local ativa.
    """

    DEFAULT_SOURCE = None # Sem câmera local
    
    def __init__(self, source = DEFAULT_SOURCE):
        """ Inicializa os estados de controle, sincronização e a origem do vídeo.

        Args:
            source (int | str | None): Identificador da câmera local (ex: 0) ou url. 
            O padrão é DEFAULT_SOURCE (processamento por push de frames).
        """
        self.current_face_encoding = None
        self._is_encoding_captured = False
        self._video_capture = None
        self.frame = None
        self._face_locations = None
        self._is_running = False
        self._thread = None
        self._lock = threading.Lock()
        self.source = source
        self._on_face_detected = None

    def start_detection(self):
        """ Inicia o ciclo de detecção facial de forma assíncrona (não-bloqueante).

        Instancia e dispara uma thread em segundo plano para rodar o loop de processamento visual.
        """
        if self._is_running:
            return

        self._is_running = True
        self._thread = threading.Thread(target=self.__face_detection, daemon=True)
        self._thread.start()

    def stop_detection(self):
        """ Interrompe o ciclo de detecção e libera todos os recursos.
        """
        self._is_running = False

        if self._thread:
            self._thread.join() # Aguarda a thread finalizar
            self._thread = None

        if self._video_capture:
            self._video_capture.release()
            cv2.destroyAllWindows()

    def clear_encoding(self):
        with self._lock:
            self.current_face_encoding = None

    def push_frame(self, frame):
        """ Injeta um frame capturado por uma fonte externa.

        Utilizado quando o robô recebe imagens através de protocolos de rede (ex: WebSockets), 
        substituindo a necessidade de uma webcam local conectada diretamente.

        Args:
            frame (numpy.ndarray): Vetor da imagem decodificada no formato BGR.
        """
        with self._lock:
            self.frame = frame

    def __face_detection(self):
        """ Executa o loop contínuo de captura, amostragem e codificação facial.

        Executado na thread paralela. Se uma fonte local (`source`) for declarada, 
        faz a leitura física do dispositivo.
        """
        
        if self.source is not None:
            # Inicia a captura de vídeo
            self._video_capture = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)

        while self._is_running:

            if self.source is not None:
                
                # Captura um único frame (quadro) de vídeo junto a uma flag indicando se ele foi de fato capturado
                ret, frame = self._video_capture.read()
                
                # Se houver algum erro de comunicação com a câmera, encerra
                if not ret or frame is None:
                    print("Erro ao acessar a câmera ou ao realizar captura.")
                    break

                with self._lock:
                    self.frame = frame

            with self._lock:
                frame = self.frame

            if frame is None:
                time.sleep(0.02)
                continue

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
                        
                        if self._on_face_detected:
                            self._on_face_detected()

            else: # Se não houver nenhum rosto
                self._is_encoding_captured = False

            time.sleep(0.02)

    def __process_frame(self, frame):
        """ Processa o frame reduzindo a resolução e convertendo o mapa de cores.

        O redimensionamento reduz os pixels totais da imagem original, acelerando 
        o cálculo de localização. Ajusta também o canal padrão do OpenCV (BGR) para 
        o exigido pela biblioteca dlib/face_recognition (RGB).

        Args:
            frame (numpy.ndarray): Vetor da imagem original capturada.

        Returns:
            Frame processado.
        """

        # Reduzindo o tamanho da imagem para 1/4 para processar mais rápido
        resized_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # A biblioteca face_recognition trabalha com RGB. É necessário converter:
        resized_frame_rgb = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)

        return resized_frame_rgb
    
    def set_face_callback(self, callback):
        """Registra o callback a ser invocado quando um rosto é detectado.

        Args:
            callback: Função a ser chamada ao detectar um rosto pela primeira vez.
        """
        self._on_face_detected = callback