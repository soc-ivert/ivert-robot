'use strict';

function speak(text) {

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'pt-BR';
    utterance.onend = () => {
        send({ type: 'speech_end' });
    };

    speechSynthesis.speak(utterance);
}

export { speak };