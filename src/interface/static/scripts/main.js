'use strict';

import { connect } from './websocket.js';
import { startListening, ttsWarmup } from './speech.js';

ttsWarmup();
connect();
startListening();