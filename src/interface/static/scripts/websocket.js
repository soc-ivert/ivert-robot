'use strict';

const WS_URL = `wss://${location.host}/ws`;
const FRAME_WIDTH = 320; 
const FRAME_HEIGHT = 240; 
const FRAME_RATE = 15;     // quantos frames por segundo enviar ao servidor
const JPEG_QUALITY = 0.5;  // qualidade do JPEG: 0.0 (mínimo) a 1.0 (máximo)

const video  = document.getElementById('video');
const canvas = document.getElementById('canvas');
const status = document.getElementById('status');

// Define o tamanho do canvas e obtem o contexto 2d
canvas.width  = FRAME_WIDTH;
canvas.height = FRAME_HEIGHT;
const ctx = canvas.getContext('2d');

// Abre a conexão com o servidor pelo WebSocket assim que o script carrega.
const ws = new WebSocket(WS_URL);

ws.onopen = () => {
    status.textContent = 'Conectado ao servidor.';
    startVideoCapture();
};

ws.onclose = () => {
    status.textContent = 'Conexão encerrada.';
};

ws.onerror = (erro) => {
    status.textContent = 'Erro na conexão WebSocket.';
};

ws.onmessage = (event) => {

    const { type, data } = JSON.parse(event.data);

    const handlers = {
        resposta: () => falar(data.text)
    };

    handlers[type]?.();

}

async function startVideoCapture() {

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: FRAME_WIDTH, height: FRAME_HEIGHT },
            audio: false,
        });

        // Conecta o stream ao elemento <video>
        video.srcObject = stream;
        await video.play();

        status.textContent = 'Câmera ativa. Enviando frames...';

        // Inicia o envio de frames no intervalo definido por FRAME_RATE
        setInterval(sendFrames, Math.round(1000 / FRAME_RATE));

    } catch (error) {
        status.textContent = 'Erro ao acessar câmera: ' + error.message;
    }
}

function sendFrames() {
   
    if (ws.readyState !== WebSocket.OPEN) 
        return;

    // Só envia se o vídeo já estiver reproduzindo (tem dimensões)
    if (!video.videoWidth) 
        return;

    // Desenha o frame atual do <video> no <canvas>
    ctx.drawImage(video, 0, 0, FRAME_WIDTH, FRAME_HEIGHT);

    // Converte o canvas para uma string Base64 no formato JPEG.
    const base64 = canvas.toDataURL('image/jpeg', JPEG_QUALITY).split(',')[1];

    ws.send(JSON.stringify({ tipo: "frame", dados: { imagem: base64}})); // Envia para o servidor pelo WebSocket
}

/* Somente para testar
*/
function falar(texto) {
    const utterance = new SpeechSynthesisUtterance(texto);
    utterance.lang = "pt-BR";
    speechSynthesis.speak(utterance);
}

function perguntar() {
    const input = document.getElementById("input-texto");
    const texto = input.value.trim();
    if (!texto) return;

    ws.send(JSON.stringify({ tipo: "ask", dados: { texto } }));
    input.value = "";
}

document.getElementById("input-texto").addEventListener("keydown", (e) => {
    if (e.key === "Enter") perguntar();
});
