'use strict';

import { connect } from './websocket.js';
import { startListening } from './speech.js';

connect();
startListening();