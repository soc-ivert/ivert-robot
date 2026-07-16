'use strict';

import { startCamera } from './camera.js';
import { speak } from './speech.js';
import { setState } from './ui.js';

const status = document.getElementById('ws-status');
const WS_URL = `wss://${location.host}/ws`;
let ws;
let reconnectTimeout = null; // Mantém a referência do timer
let retryDelay = 1000; // Tempo de espera inicial para tentativa de reconexão (1s)

function connect() {

    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
    }

    status.textContent = 'Conectando ao servidor...';
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        status.textContent = 'Conectado ao servidor.';
        retryDelay = 1000; // Reseta o atraso após uma conexão de sucesso
        startCamera(send);
    };

    ws.onclose = () => {
        status.textContent = `Conexão fechada. Reconectando em ${retryDelay / 1000}s...`;
        scheduleReconnect(); // Dispara agendamento de nova tentativa de reconexão
    };

    ws.onerror = () => {
        status.textContent = 'Erro de conexão';
    };

    ws.onmessage = (event) => {

        const { type, data } = JSON.parse(event.data);

        const handlers = {
            answer: () => speak(data.text),
            state: () => setState(data.value),
        };

        handlers[type]?.();
    };
}

// Agenda uma reconexão
function scheduleReconnect() {

    if (reconnectTimeout)
        return;

    reconnectTimeout = setTimeout(() => {
        reconnectTimeout = null;
        connect();
    }, retryDelay);

    // Dobra o delay a cada falha, limitando o tempo máximo a 16 segundos
    retryDelay = Math.min(retryDelay * 2, 16000);
}

function send(payload) {
    if (ws?.readyState === WebSocket.OPEN)
        ws.send(JSON.stringify(payload));
}

export { connect, send };