'use strict';

import { startCamera } from './camera.js';
import { speak } from './speech.js';
import { setState } from './ui.js';

const status = document.getElementById('ws-status');
const WS_URL = `wss://${location.host}/ws`;
let ws;

function connect() {

    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        status.textContent = 'Conectado ao servidor.';
        startCamera(send);
    };

    ws.onclose = () => status.textContent = 'Conexão fechada';
    ws.onerror = () => status.textContent = 'Erro de conexão';

    ws.onmessage = (event) => {

        const { type, data } = JSON.parse(event.data);

        const handlers = {
            answer: () => speak(data.text),
            state:  () => setState(data.value),
        };

        handlers[type]?.();
    };
}

function send(payload) {
    if (ws?.readyState === WebSocket.OPEN)
        ws.send(JSON.stringify(payload));
}

export { connect, send };