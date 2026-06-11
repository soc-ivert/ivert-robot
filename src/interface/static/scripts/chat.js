'use strict';

/*** Provisório ***/

import { send } from './websocket.js';

function ask() {
    const input = document.getElementById('input-texto');
    const text  = input.value.trim();
    if (!text) return;

    send({ type: 'ask', data: { text } });
    input.value = '';
}

function initChat() {
    document.getElementById('input-texto').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') ask();
    });

    // Expõe para o onclick do HTML
    window.ask = ask;
}

export { ask, initChat };