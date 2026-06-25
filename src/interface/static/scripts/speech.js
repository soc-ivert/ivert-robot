'use strict';

import { send } from './websocket.js';

let isSpeaking = false;

const recognition = new webkitSpeechRecognition();
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
    if(!isSpeaking) 
        recognition.start();
};

function startListening() {
    recognition.start();
}

function speak(text) {

    if(text === "error")
        text = "Estou indisponível no momento, tente falar comigo mais tarde";

    isSpeaking = true;
    recognition.stop();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR';
    utterance.onend = () => {
        send({ type: 'speech_end' });
        isSpeaking = false;
        recognition.start();
    };

    speechSynthesis.speak(utterance);
}

export { speak, startListening };