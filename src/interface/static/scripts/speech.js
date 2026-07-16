'use strict';

import { send } from './websocket.js';

const speakStatus = document.getElementById('speak-status');
let isSpeaking = false;
let activeUtterance = null; // Mantém a referência da utterance global 

const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechAPI) {
    speakStatus.textContent = "API de Reconhecimento de Voz Indisponível";
}

const recognition = SpeechAPI ? new SpeechAPI() : null;

if (recognition) {

    recognition.lang = 'pt-BR';
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.onresult = (event) => {

        const text = event.results[event.results.length - 1][0].transcript;

        send({
            type: 'ask',
            data: { text }
        });
    };

    recognition.onend = () => {
        if (!isSpeaking)
            recognition.start();
    };
}

function startListening() {
    if (recognition)
        recognition.start();
}

function speak(text) {

    if (text === "error")
        text = "Estou indisponível no momento, tente falar comigo mais tarde";

    isSpeaking = true;
    if (recognition)
        recognition.stop();

    // Cancela qualquer fala anterior
    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR';

    // Armazena a referência globalmente para evitar o Garbage Collector do navegador durante a fala
    activeUtterance = utterance;

    // Limpa o estado e reinicia o reconhecimento de voz
    const handleSpeechFinished = () => {

        activeUtterance = null;
        send({ type: 'speech_end' });
        isSpeaking = false;

        if (recognition)
            recognition.start();
    };

    utterance.onend = () => {
        speakStatus.textContent = "Acabou de falar";
        handleSpeechFinished();
    };

    // Garante que o robô não fique preso no estado SPEAKING caso o navegador falhe ao falar
    utterance.onerror = (err) => {
        speakStatus.textContent = "Erro de fala";
        handleSpeechFinished();
    };

    speakStatus.textContent = "Falando";
    speechSynthesis.speak(utterance);
}

export { speak, startListening };