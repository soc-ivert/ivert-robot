'use strict';

const stage = document.getElementById('stage') || document.body;
const stateEl = document.getElementById('bot-state');
const greetingTextEl = document.getElementById('greeting-text');

const VALID_STATES = new Set(['sleeping', 'greeting', 'waiting', 'thinking', 'speaking']);

let currentState = null;
let transitionTimeout = null;

/**
 * Prepara as letras do texto de saudação em spans individuais
 * para permitir a animação de "pulinho" em cascata / onda.
 */
function prepareGreetingText() {
  if (!greetingTextEl) return;
  const rawText = greetingTextEl.textContent.trim();
  greetingTextEl.innerHTML = '';

  let charIdx = 0;
  for (const char of rawText) {
    const span = document.createElement('span');
    span.className = 'greeting-char';
    if (char === ' ') {
      span.innerHTML = '&nbsp;';
    } else {
      span.textContent = char;
    }
    span.style.setProperty('--char-index', charIdx);
    greetingTextEl.appendChild(span);
    charIdx++;
  }
}

/**
 * Remove todas as classes de estado e transição da cena.
 */
function clearAllStateClasses() {
  const classesToRemove = [];
  for (const cls of stage.classList) {
    if (cls.startsWith('state-') || cls.startsWith('trans-')) {
      classesToRemove.push(cls);
    }
  }
  for (const cls of classesToRemove) {
    stage.classList.remove(cls);
  }
}

/**
 * Atualiza o indicador de debug
 */
function updateDebug(state) {
  if (stateEl) {
    stateEl.textContent = state.toUpperCase();
  }
}

/**
 * Aplica um estado diretamente sem transição composta
 */
function applyStateDirect(state) {
  clearAllStateClasses();
  void stage.offsetWidth; // Força reflow para CSS animations dispararem
  stage.classList.add(`state-${state}`);
  currentState = state;
  updateDebug(state);
}

/**
 * setState(state)
 * Controla a expressão visual do robô com transições fluidas.
 * 
 * Regras especiais de transição:
 * 1. GREETING -> THINKING: O formato dos olhos se estreita formando o círculo (oval)
 *    primeiro, e então se desloca para cima/esquerda em direção ao balão de pensamento.
 * 2. WAITING -> SLEEPING: Efeito de desligamento (power-off) nos olhos antes do ZZZ entrar.
 * 3. GREETING -> DEMAIS ESTADOS: Morfologia suave dos arcos para os olhos ovais.
 * 4. DEMAIS ESTADOS: Transição suave entre saída e entrada.
 */
function setState(state) {
  if (!state) return;
  if (!VALID_STATES.has(state)) {
    console.warn(`[UI] Estado desconhecido: "${state}"`);
    return;
  }

  if (state === currentState && !transitionTimeout) return;

  // Cancela qualquer transição intermediária pendente se um novo estado for solicitado rapidamente
  if (transitionTimeout) {
    clearTimeout(transitionTimeout);
    transitionTimeout = null;
  }

  const prevState = currentState;

  // CASO 1: greeting -> thinking (morfologia para oval primeiro, depois move e surge o balão)
  if (prevState === 'greeting' && state === 'thinking') {
    clearAllStateClasses();
    stage.classList.add('trans-greeting-to-thinking-step1');
    updateDebug('thinking (trans)');

    transitionTimeout = setTimeout(() => {
      transitionTimeout = null;
      applyStateDirect('thinking');
    }, 280);
    return;
  }

  // CASO 2: waiting -> sleeping (efeito de desligar / power-off nos olhos antes de dormir)
  if (prevState === 'waiting' && state === 'sleeping') {
    clearAllStateClasses();
    stage.classList.add('trans-power-off');
    updateDebug('sleeping (trans)');

    transitionTimeout = setTimeout(() => {
      transitionTimeout = null;
      applyStateDirect('sleeping');
    }, 340);
    return;
  }

  // CASO 3: sleeping -> greeting (ZZZ desliga -> olhos abertos 1.5s -> arcos felizes)
  if (prevState === 'sleeping' && state === 'greeting') {
    // Step 1: ZZZ power-off (desliga quase imediatamente)
    clearAllStateClasses();
    stage.classList.add('trans-sleep-greet-step1');
    updateDebug('greeting (trans)');

    transitionTimeout = setTimeout(() => {
      // Step 2: Eyes open (como waiting) por 1.5 segundos
      clearAllStateClasses();
      void stage.offsetWidth;
      stage.classList.add('trans-sleep-greet-step2');

      transitionTimeout = setTimeout(() => {
        // Step 3: Eyes close into greeting arcs + banner
        clearAllStateClasses();
        void stage.offsetWidth;
        stage.classList.add('trans-sleep-greet-step3');

        transitionTimeout = setTimeout(() => {
          transitionTimeout = null;
          applyStateDirect('greeting');
        }, 350);
      }, 1500);
    }, 150);
    return;
  }

  // CASO 4: greeting -> waiting ou speaking (morfologia suave de arcos para ovais)
  if (prevState === 'greeting' && (state === 'waiting' || state === 'speaking')) {
    clearAllStateClasses();
    stage.classList.add('trans-greeting-morph');
    updateDebug(`${state} (trans)`);

    transitionTimeout = setTimeout(() => {
      transitionTimeout = null;
      applyStateDirect(state);
    }, 260);
    return;
  }

  // Transição padrão suave para todos os outros casos
  applyStateDirect(state);
}

// Inicialização
prepareGreetingText();
setState('sleeping');

export { setState };