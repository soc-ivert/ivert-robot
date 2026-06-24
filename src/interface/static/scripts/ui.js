'use strict';

var botState = document.getElementById('bot-state');

function setState(state){
    botState.textContent = state
}

export { setState };