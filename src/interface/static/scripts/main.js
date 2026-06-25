'use strict';

import { connect } from './websocket.js';
import { initChat } from './chat.js';
import { startListening } from './speech.js';

connect();
initChat();
startListening();