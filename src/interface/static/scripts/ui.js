'use strict';

const face       = document.getElementById('face');
const stateEl    = document.getElementById('bot-state');
const stateLabel = document.getElementById('state-label');
const dot3       = document.getElementById('status-dot-3');

const VALID_STATES = new Set(['sleeping', 'greeting', 'waiting', 'thinking', 'speaking']);

const STATE_ICONS = {
  sleeping: '◌',
  greeting: '◈',
  waiting:  '◎',
  thinking: '◉',
  speaking: '▶',
};

let currentState = null;

function clearFaceClasses() {
  for (const cls of [...face.classList]) {
    if (cls.startsWith('state-')) face.classList.remove(cls);
  }
}

function updateDebug(state) {
  stateEl.textContent = state.toUpperCase();
}

function updateStatusBar(state) {
  const icon = STATE_ICONS[state] ?? '○';
  stateLabel.textContent = `${icon} ${state}`;
  dot3.classList.toggle('active', state !== 'sleeping');
}

/**
 * setState(state)
 * Muda a expressão do robô e atualiza o painel de debug.
 * Chamado pelo WebSocket handler em main.js.
 */
function setState(state) {
  if (!VALID_STATES.has(state)) {
    console.warn(`[Ivert UI] Estado desconhecido: "${state}"`);
    return;
  }
  if (state === currentState) return;

  clearFaceClasses();
  void face.offsetWidth; // força reflow para transitions CSS dispararem
  face.classList.add(`state-${state}`);
  currentState = state;
  updateDebug(state);
  updateStatusBar(state);
}

setState('sleeping');

export { setState };