'use strict';

import { send } from './websocket.js';

const speakStatus = document.getElementById('speak-status');

let isSpeaking = false;
let activeUtterance = null; // Mantém a referência da utterance global 

const SpeechAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechAPI) {
    if (speakStatus) speakStatus.textContent = "API de Reconhecimento de Voz Indisponível";
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

/* Versão adaptada para o fully kiosk */
function speak(text) {

    if (text === "error")
        text = "Estou indisponível no momento, tente falar comigo mais tarde";

    isSpeaking = true;
    if (recognition)
        recognition.stop();

    // Limpa o estado e reinicia o reconhecimento de voz
    const handleSpeechFinished = () => {
        activeUtterance = null;
        send({ type: 'speech_end' });
        isSpeaking = false;

        if (recognition)
            recognition.start();
    };

    // Verifica se a JS Interface do Fully Kiosk está disponível
    if (typeof fully === 'undefined' || typeof fully.textToSpeech !== 'function') {
        console.error('Fully JavaScript Interface indisponível — TTS não pôde ser executado.');
        handleSpeechFinished();
        return;
    }

    // Usada apenas uma flag de controle de estado, não como referência de objeto (diferente da Web Speech API original)
    activeUtterance = text;
    fully.textToSpeech(text);

    // Estima a duração da fala com base no tamanho do texto, já que a API do Fully não expõe evento de término
    const CARACTERES_POR_SEGUNDO = 15;
    const MARGEM_SEGURANCA_MS = 400;   // evita cortar a fala um pouco antes do fim
    const duracaoEstimadaMs = (text.length / CARACTERES_POR_SEGUNDO) * 1000 + MARGEM_SEGURANCA_MS;

    setTimeout(handleSpeechFinished, duracaoEstimadaMs);
}

/* Versão da função que utiliza SpeechSynthesisUtterance (Incompativel com WebView)
function speak(text) {

    if (text === "error")
        text = "Estou indisponível no momento, tente falar comigo mais tarde";

    isSpeaking = true;
    if (recognition)
        recognition.stop();


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
*/

// Usada para "acordar" o TTS da WebView, evitando delays de inicialização.
function ttsWarmup() {

    if (typeof fully !== 'undefined' && typeof fully.textToSpeech === 'function')
        fully.textToSpeech(" ");

}

export { speak, startListening, ttsWarmup };