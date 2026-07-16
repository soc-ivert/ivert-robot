'use strict';

const FRAME_WIDTH = 320;
const FRAME_HEIGHT = 240;
const FRAME_RATE = 15; // quantos frames por segundo enviar ao servidor
const JPEG_QUALITY = 0.5; // qualidade do JPEG: 0.0 (mínimo) a 1.0 (máximo)

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const status = document.getElementById('camera-status');
let frameInterval = null; // Armazena o ID do intervalo ativo para evitar loops simultâneos de envio de frame

canvas.width = FRAME_WIDTH;
canvas.height = FRAME_HEIGHT;


async function startCamera(send) {
    try {
        // Cancela o intervalo de envio de frames anterior se já estiver ativo (ex: após reconexão)
        if (frameInterval) {
            clearInterval(frameInterval);
            frameInterval = null;
        }

        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'user',
                width: FRAME_WIDTH,
                height: FRAME_HEIGHT
            },
            audio: false,
        });

        video.srcObject = stream;
        await video.play();

        // Inicia o envio de frames ao servidor em intervalos regulares
        frameInterval = setInterval(() => sendFrame(send), Math.round(1000 / FRAME_RATE));
        status.textContent = "Camera ativa. Enviando frames...";

    } catch (error) {
        status.textContent = "Erro na camera: " + error.message;
    }
}

function sendFrame(send) {

    if (!video.videoWidth)
        return;

    ctx.drawImage(video, 0, 0, FRAME_WIDTH, FRAME_HEIGHT);
    const image = canvas.toDataURL('image/jpeg', JPEG_QUALITY).split(',')[1];

    send({
        type: 'frame',
        data: { image }
    });
}

export { startCamera };