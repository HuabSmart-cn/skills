/**
 * Chrome WebSocket Library - Core CDP automation functions
 * Used by both CLI and MCP server
 *
 * Fixes implemented:
 * - JRV-130: Connection pooling for persistent focus
 * - JRV-127: keyboard_press action for special keys
 * - JRV-123: React-compatible input via Input.insertText
 * - JRV-124: React-compatible click via Input.dispatchMouseEvent
 * - JRV-125: Tab key handling (via keyboard_press)
 * - JRV-126: Better eval return handling
 * - JRV-128: SPA navigation support
 * - JRV-129: Multi-element selector warnings
 */

const http = require('http');
const crypto = require('crypto');

const {
  CHROME_DEBUG_HOST,
  CHROME_DEBUG_PORT,
  rewriteWsUrl
} = require('./host-override');

// Minimal WebSocket client implementation (dependency-free)
class WebSocketClient {
  constructor(url) {
    this.url = new URL(url);
    this.callbacks = {};
    this.socket = null;
    this.buffer = Buffer.alloc(0);
    this.connected = false;
  }

  on(event, callback) {
    this.callbacks[event] = callback;
  }

  isConnected() {
    return this.connected && this.socket !== null;
  }

  connect() {
    return new Promise((resolve, reject) => {
      const key = crypto.randomBytes(16).toString('base64');

      const options = {
        hostname: this.url.hostname,
        port: this.url.port || 80,
        path: this.url.pathname + this.url.search,
        headers: {
          'Upgrade': 'websocket',
          'Connection': 'Upgrade',
          'Sec-WebSocket-Key': key,
          'Sec-WebSocket-Version': '13'
        }
      };

      const req = http.request(options);

      req.on('upgrade', (res, socket) => {
        this.socket = socket;
        this.connected = true;

        socket.on('data', (data) => {
          this.buffer = Buffer.concat([this.buffer, data]);
          this.processFrames();
        });

        socket.on('error', (err) => {
          this.connected = false;
          if (this.callbacks.error) this.callbacks.error(err);
        });

        socket.on('close', () => {
          this.connected = false;
          if (this.callbacks.close) this.callbacks.close();
        });

        if (this.callbacks.open) this.callbacks.open();
        resolve();
      });

      req.on('error', reject);
      req.end();
    });
  }

  processFrames() {
    while (this.buffer.length >= 2) {
      const firstByte = this.buffer[0];
      const secondByte = this.buffer[1];

      const fin = (firstByte & 0x80) !== 0;
      const opcode = firstByte & 0x0F;
      const masked = (secondByte & 0x80) !== 0;
      let payloadLen = secondByte & 0x7F;

      let offset = 2;

      if (payloadLen === 126) {
        if (this.buffer.length < 4) return;
        payloadLen = this.buffer.readUInt16BE(2);
        offset = 4;
      } else if (payloadLen === 127) {
        if (this.buffer.length < 10) return;
        payloadLen = Number(this.buffer.readBigUInt64BE(2));
        offset = 10;
      }

      if (this.buffer.length < offset + payloadLen) return;

      let payload = this.buffer.slice(offset, offset + payloadLen);
      this.buffer = this.buffer.slice(offset + payloadLen);

      if (opcode === 0x1 && this.callbacks.message) {
        this.callbacks.message(payload.toString('utf8'));
      }
    }
  }

  send(data) {
    if (!this.socket || !this.connected) {
      throw new Error('WebSocket not connected');
    }
    const payload = Buffer.from(data, 'utf8');
    const payloadLen = payload.length;

    let frame;
    let offset = 2;

    if (payloadLen < 126) {
      frame = Buffer.alloc(payloadLen + 6);
      frame[1] = payloadLen | 0x80;
    } else if (payloadLen < 65536) {
      frame = Buffer.alloc(payloadLen + 8);
      frame[1] = 126 | 0x80;
      frame.writeUInt16BE(payloadLen, 2);
      offset = 4;
    } else {
      frame = Buffer.alloc(payloadLen + 14);
      frame[1] = 127 | 0x80;
      frame.writeBigUInt64BE(BigInt(payloadLen), 2);
      offset = 10;
    }

    frame[0] = 0x81; // FIN + text frame

    const mask = Buffer.alloc(4);
    crypto.randomFillSync(mask);
    mask.copy(frame, offset);
    offset += 4;

    for (let i = 0; i < payloadLen; i++) {
      frame[offset + i] = payload[i] ^ mask[i % 4];
    }

    this.socket.write(frame);
  }

  close() {
    this.connected = false;
    if (this.socket) {
      this.socket.end();
      this.socket = null;
    }
  }
}

// =============================================================================
// CONNECTION POOL (JRV-130: Fix focus lost between eval calls)
// =============================================================================

// Connection pool: maintains persistent WebSocket connections per tab
const connectionPool = new Map(); // wsUrl -> { ws: WebSocketClient, pendingRequests: Map, messageIdCounter: number }

/**
 * Get or create a pooled connection for a tab
 */
async function getPooledConnection(wsUrl) {
  let conn = connectionPool.get(wsUrl);

  if (conn && conn.ws.isConnected()) {
    return conn;
  }

  // Create new connection
  const ws = new WebSocketClient(wsUrl);
  conn = {
    ws,
    pendingRequests: new Map(), // id -> { resolve, reject, timeout }
    messageIdCounter: 1
  };

  ws.on('message', (msg) => {
    try {
      const data = JSON.parse(msg);
      if (data.id !== undefined) {
        const pending = conn.pendingRequests.get(data.id);
        if (pending) {
          clearTimeout(pending.timeout);
          conn.pendingRequests.delete(data.id);
          if (data.error) {
            pending.reject(new Error(data.error.message || JSON.stringify(data.error)));
          } else {
            pending.resolve(data.result);
          }
        }
      }
      // Handle events (console messages, etc.)
      if (data.method && conn.eventHandler) {
        conn.eventHandler(data);
      }
    } catch (e) {
      console.error('Error processing CDP message:', e);
    }
  });

  ws.on('close', () => {
    connectionPool.delete(wsUrl);
    // Reject all pending requests
    for (const [id, pending] of conn.pendingRequests) {
      clearTimeout(pending.timeout);
      pending.reject(new Error('Connection closed'));
    }
    conn.pendingRequests.clear();
  });

  ws.on('error', (err) => {
    console.error('WebSocket error:', err);
  });

  await ws.connect();
  connectionPool.set(wsUrl, conn);

  return conn;
}

/**
 * Send CDP command using pooled connection (maintains focus/state)
 */
async function sendCdpCommandPooled(wsUrl, method, params = {}, timeout = 30000) {
  const conn = await getPooledConnection(wsUrl);
  const id = conn.messageIdCounter++;

  return new Promise((resolve, reject) => {
    const timeoutHandle = setTimeout(() => {
      conn.pendingRequests.delete(id);
      reject(new Error(`CDP command timeout: ${method}`));
    }, timeout);

    conn.pendingRequests.set(id, { resolve, reject, timeout: timeoutHandle });
    conn.ws.send(JSON.stringify({ id, method, params }));
  });
}

/**
 * Close pooled connection for a tab
 */
function closePooledConnection(wsUrl) {
  const conn = connectionPool.get(wsUrl);
  if (conn) {
    conn.ws.close();
    connectionPool.delete(wsUrl);
  }
}

/**
 * Close all pooled connections
 */
function closeAllConnections() {
  for (const [wsUrl, conn] of connectionPool) {
    conn.ws.close();
  }
  connectionPool.clear();
}

// Helper to make HTTP requests to Chrome
async function chromeHttp(path, method = 'GET') {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: CHROME_DEBUG_HOST,
      port: CHROME_DEBUG_PORT,
      path,
      method: method
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (!data) {
          resolve({});
          return;
        }
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          // Some endpoints return plain text (e.g., "Target is closing")
          resolve({ message: data });
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

// Console message storage per tab
const consoleMessages = new Map();

// Session management - uses XDG cache directories
let sessionDir = null;
let captureCounter = 0;

// Chrome process management
let chromeProcess = null;
let chromeHeadless = true; // Default to headless mode
let chromeUserDataDir = null;
let chromeProfileName = 'superpowers-chrome'; // Default profile name

// Helper to resolve tab index or ws URL to actual ws URL
async function resolveWsUrl(wsUrlOrIndex) {
  // If it's already a WebSocket URL, rewrite and return it
  if (typeof wsUrlOrIndex === 'string' && wsUrlOrIndex.startsWith('ws://')) {
    return rewriteWsUrl(wsUrlOrIndex);
  }

  // If it's a number (tab index), resolve it
  const index = typeof wsUrlOrIndex === 'number' ? wsUrlOrIndex : parseInt(wsUrlOrIndex);
  if (!isNaN(index)) {
    const tabs = await chromeHttp('/json');
    const pageTabs = tabs.filter(t => t.type === 'page');

    // Auto-create tab if none exist (similar to auto-start Chrome behavior)
    if (pageTabs.length === 0) {
      const newTabInfo = await newTab();
      return newTabInfo.webSocketDebuggerUrl;
    }

    if (index < 0 || index >= pageTabs.length) {
      throw new Error(`Tab index ${index} out of range (0-${pageTabs.length - 1})`);
    }
    return pageTabs[index].webSocketDebuggerUrl;
  }

  throw new Error(`Invalid tab specifier: ${wsUrlOrIndex}`);
}

// Message ID counter for legacy single-use connections
let messageIdCounter = 1;

// Helper to generate element selection code (supports CSS and XPath)
function getElementSelector(selector) {
  if (selector.startsWith('/') || selector.startsWith('//')) {
    // XPath selector
    return `document.evaluate(${JSON.stringify(selector)}, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue`;
  } else {
    // CSS selector
    return `document.querySelector(${JSON.stringify(selector)})`;
  }
}

// Helper to get all matching elements (for JRV-129 warnings)
function getElementSelectorAll(selector) {
  if (selector.startsWith('/') || selector.startsWith('//')) {
    // XPath - get all matches
    return `(() => {
      const result = [];
      const iterator = document.evaluate(${JSON.stringify(selector)}, document, null, XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
      let node;
      while (node = iterator.iterateNext()) result.push(node);
      return result;
    })()`;
  } else {
    // CSS selector
    return `Array.from(document.querySelectorAll(${JSON.stringify(selector)}))`;
  }
}

/**
 * Send CDP command using pooled connection (default - maintains focus)
 * Falls back to single-use connection if pool fails
 */
async function sendCdpCommand(wsUrl, method, params = {}, timeout = 30000) {
  try {
    return await sendCdpCommandPooled(wsUrl, method, params, timeout);
  } catch (e) {
    // Fallback to single-use connection for reliability
    console.error('Pooled connection failed, using single-use:', e.message);
    return await sendCdpCommandSingle(wsUrl, method, params, timeout);
  }
}

/**
 * Legacy single-use connection (for backwards compatibility)
 */
async function sendCdpCommandSingle(wsUrl, method, params = {}, timeout = 30000) {
  const ws = new WebSocketClient(wsUrl);

  return new Promise((resolve, reject) => {
    const id = messageIdCounter++;
    let resolved = false;

    ws.on('message', (msg) => {
      const data = JSON.parse(msg);
      if (data.id === id) {
        resolved = true;
        ws.close();
        if (data.error) {
          reject(new Error(data.error.message || JSON.stringify(data.error)));
        } else {
          resolve(data.result);
        }
      }
    });

    ws.on('error', (err) => {
      if (!resolved) {
        reject(err);
      }
    });

    ws.connect()
      .then(() => {
        ws.send(JSON.stringify({ id, method, params }));
      })
      .catch(reject);

    setTimeout(() => {
      if (!resolved) {
        ws.close();
        reject(new Error('CDP command timeout'));
      }
    }, timeout);
  });
}

// =============================================================================
// KEY NAME MAPPINGS (JRV-127: keyboard.press support)
// =============================================================================

// Map common key names to CDP key codes
const KEY_DEFINITIONS = {
  // Navigation keys
  'Tab': { key: 'Tab', code: 'Tab', keyCode: 9 },
  'Enter': { key: 'Enter', code: 'Enter', keyCode: 13 },
  'Escape': { key: 'Escape', code: 'Escape', keyCode: 27 },
  'Backspace': { key: 'Backspace', code: 'Backspace', keyCode: 8 },
  'Delete': { key: 'Delete', code: 'Delete', keyCode: 46 },
  'Space': { key: ' ', code: 'Space', keyCode: 32 },

  // Arrow keys
  'ArrowUp': { key: 'ArrowUp', code: 'ArrowUp', keyCode: 38 },
  'ArrowDown': { key: 'ArrowDown', code: 'ArrowDown', keyCode: 40 },
  'ArrowLeft': { key: 'ArrowLeft', code: 'ArrowLeft', keyCode: 37 },
  'ArrowRight': { key: 'ArrowRight', code: 'ArrowRight', keyCode: 39 },

  // Modifier keys
  'Shift': { key: 'Shift', code: 'ShiftLeft', keyCode: 16 },
  'Control': { key: 'Control', code: 'ControlLeft', keyCode: 17 },
  'Alt': { key: 'Alt', code: 'AltLeft', keyCode: 18 },
  'Meta': { key: 'Meta', code: 'MetaLeft', keyCode: 91 },

  // Function keys
  'F1': { key: 'F1', code: 'F1', keyCode: 112 },
  'F2': { key: 'F2', code: 'F2', keyCode: 113 },
  'F3': { key: 'F3', code: 'F3', keyCode: 114 },
  'F4': { key: 'F4', code: 'F4', keyCode: 115 },
  'F5': { key: 'F5', code: 'F5', keyCode: 116 },
  'F6': { key: 'F6', code: 'F6', keyCode: 117 },
  'F7': { key: 'F7', code: 'F7', keyCode: 118 },
  'F8': { key: 'F8', code: 'F8', keyCode: 119 },
  'F9': { key: 'F9', code: 'F9', keyCode: 120 },
  'F10': { key: 'F10', code: 'F10', keyCode: 121 },
  'F11': { key: 'F11', code: 'F11', keyCode: 122 },
  'F12': { key: 'F12', code: 'F12', keyCode: 123 },

  // Other
  'Home': { key: 'Home', code: 'Home', keyCode: 36 },
  'End': { key: 'End', code: 'End', keyCode: 35 },
  'PageUp': { key: 'PageUp', code: 'PageUp', keyCode: 33 },
  'PageDown': { key: 'PageDown', code: 'PageDown', keyCode: 34 },
  'Insert': { key: 'Insert', code: 'Insert', keyCode: 45 },
};

// API Functions

async function getTabs() {
  const tabs = await chromeHttp('/json');
  if (!Array.isArray(tabs)) {
    return [];
  }
  return tabs
    .filter(tab => tab.type === 'page')
    .map(tab => ({
      ...tab,
      webSocketDebuggerUrl: rewriteWsUrl(tab.webSocketDebuggerUrl)
    }));
}

async function newTab(url = 'about:blank') {
  const encoded = encodeURIComponent(url);
  const tab = await chromeHttp(`/json/new?${encoded}`, 'PUT');
  if (tab && typeof tab === 'object') {
    tab.webSocketDebuggerUrl = rewriteWsUrl(tab.webSocketDebuggerUrl);
  }
  return tab;
}

async function closeTab(tabIndexOrWsUrl) {
  const wsUrl = await resolveWsUrl(tabIndexOrWsUrl);
  const tabs = await chromeHttp('/json');
  const tab = tabs.find(t => t.webSocketDebuggerUrl === wsUrl);
  if (tab) {
    await chromeHttp(`/json/close/${tab.id}`, 'GET');
  }
}

async function navigate(tabIndexOrWsUrl, url, autoCapture = false) {
  const wsUrl = await resolveWsUrl(tabIndexOrWsUrl);

  // Clear previous console messages if auto-capture is on
  const startTime = new Date();
  if (autoCapture) {
    await clearConsoleMessages(tabIndexOrWsUrl);
  }

  const result = await sendCdpCommand(wsUrl, 'Page.navigate', { url });

  // Wait for page load with console logging enabled if needed
  await new Promise((resolve) => {
    const ws = new WebSocketClient(wsUrl);
    let pageLoaded = false;

    ws.on('message', (msg) => {
      const data = JSON.parse(msg);

      if (data.method === 'Page.loadEventFired' && !pageLoaded) {
        pageLoaded = true;
        // Keep connection alive a bit longer for console messages if auto-capture is on
        if (autoCapture) {
          setTimeout(() => {
            ws.close();
            resolve();
          }, 1000); // Wait 1 second for console messages
        } else {
          ws.close();
          resolve();
        }
      }

      // Capture console messages during navigation if auto-capture is on
      if (autoCapture && data.method === 'Runtime.consoleAPICalled') {
        const entry = data.params;
        const timestamp = new Date().toISOString();
        const level = entry.type || 'log';
        const args = entry.args || [];

        // Extract text from arguments
        const text = args.map(arg => {
          if (arg.type === 'string') return arg.value;
          if (arg.type === 'number') return String(arg.value);
          if (arg.type === 'boolean') return String(arg.value);
          if (arg.type === 'object') return arg.description || '[Object]';
          return String(arg.value || arg.description || arg.type);
        }).join(' ');

        const messages = consoleMessages.get(wsUrl) || [];
        messages.push({
          timestamp,
          level,
          text
        });
        consoleMessages.set(wsUrl, messages);
      }
    });

    ws.connect().then(() => {
      // Enable both Page and Runtime domains
      sendCdpCommand(wsUrl, 'Page.enable');
      if (autoCapture) {
        sendCdpCommand(wsUrl, 'Runtime.enable');
      }
    });

    // Timeout after 30s
    setTimeout(() => {
      if (!pageLoaded) {
        ws.close();
        resolve();
      }
    }, 30000);
  });

  // Auto-capture if requested
  if (autoCapture) {
    try {
      const artifacts = await capturePageArtifacts(tabIndexOrWsUrl, 'navigate');

      // TODO: Fix console logging - currently returns empty array
      // The console logging needs a persistent WebSocket connection which
      // conflicts with the current single-use connection pattern
      const consoleLog = []; // Placeholder for now

      return {
        frameId: result.frameId,
        url,
        pageSize: artifacts.pageSize,
        capturePrefix: artifacts.capturePrefix,
        sessionDir: artifacts.sessionDir,
        files: artifacts.files,
        domSummary: artifacts.domSummary,
        consoleLog
      };
    } catch (error) {
      // If auto-capture fails, still return success but with error note
      return {
        frameId: result.frameId,
        url,
        error: `Auto-capture failed: ${error.message}`
      };
    }
  }

  return result.frameId;
}

// =============================================================================
// CLICK FUNCTION (JRV-124: Now uses CDP mouse events by default)
// =============================================================================

/**
 * Click element using CDP mouse events (works with React and all frameworks)
 * Falls back to el.click() if CDP approach fails
 */
async function click(tabIndexOrWsUrl, selector) {
  const wsUrl = await resolveWsUrl(tabIndexOrWsUrl);

  try {
    // Get element's bounding box and scroll into view
    const js = `
      (() => {
        const el = ${getElementSelector(selector)};
        if (!el) return { found: false };
        el.scrollIntoView({ block: 'center', inline: 'center' });
        const rect = el.getBoundingClientRect();
        return {
          x: rect.left + rect.width / 2,
          y: rect.top + rect.height / 2,
          found: true
        };
      })()
    `;

    const result = await sendCdpCommand(wsUrl, 'Runtime.evaluate', {
      expression: js,
      returnByValue: true
    });

    if (!result.result.value || !result.result.value.found) {
      throw new Error(`Element not found: ${selector}`);
    }

    const { x, y } = result.result.value;

    // Send real mouse events (works with React synthetic events)
    await sendCdpCommand(wsUrl, 'Input.dispatchMouseEvent', {
      type: 'mousePressed',
      x,
      y,
      button: 'left',
      clickCount: 1
    });

    await sendCdpCommand(wsUrl, 'Input.dispatchMouseEvent', {
      type: 'mouseReleased',
      x,
      y,
      button: 'left',
      clickCount: 1
    });

    return { clicked: true, x, y };
  } catch (e) {
    // Fallback to el.click() for edge cases (e.g., hidden elements)
    const js = `${getElementSelector(selector)}?.click()`;
    await sendCdpCommand(wsUrl, 'Runtime.evaluate', { expression: js });
    return { clicked: true, fallback: true };
  }
}

// Legacy alias for backwards compatibility
const cdpClick = click;

// =============================================================================
// TYPE FUNCTION - Smart text input with Tab/Enter handling
// =============================================================================

/**
 * Type text into current focus (or click selector first if provided)
 *
 * Special characters:
 *   \t = Tab (moves to next field)
 *   \n = Enter (submits form, or newline in textarea)
 *
 * Examples:
 *   type(0, null, "hello")                    // type into current focus
 *   type(0, "#email", "user@example.com")     // click #email, then type
 *   type(0, "#email", "user@example.com\tpassword\n")  // type, tab, type, submit
 */
async function fill(tabIndexOrWsUrl, selector, value) {
  const wsUrl = await resolveWsUrl(tabIndexOrWsUrl);

  // If selector provided, focus it (using JS focus, not click, to avoid capture side effects)
  if (selector) {
    const focusJs = `
      (() => {
        const el = ${getElementSelector(selector)};
        if (!el) return { success: false, error: 'Element not found' };
        el.focus();
        return { success: true, focused: document.activeElement === el };
      })()
    `;
    const focusResult = await sendCdpCommand(wsUrl, 'Runtime.evaluate', {
      expression: focusJs,
      returnByValue: true
    });
    if (!focusResult.result?.value?.success) {
      throw new Error(focusResult.result?.value?.error || 'Failed to focus element');
    }
  }

  // Convert literal escape sequences to actual characters
  // (MCP payloads may contain literal \t and \n rather than actual tab/newline)
  const processedValue = value
    .replace(/\\t/g, '\t')
    .replace(/\\n/g, '\n');

  // Check if current focus is a textarea (for \n handling)
  const focusInfo = await sendCdpCommand(wsUrl, 'Runtime.evaluate', {
    expression: `({ isTextarea: document.activeElement?.tagName === 'TEXTAREA' })`,
    returnByValue: true
  });
  const isTextarea = focusInfo.result?.value?.isTextarea || false;

  // Small delay helper to let browser process input
  const settle = (ms = 50) => new Promise(r => setTimeout(r, ms));

  // Parse and type the value, handling \t and \n specially
  let buffer = '';

  for (let i = 0; i < processedValue.length; i++) {
    const char = processedValue[i];

    if (char === '\t') {
      // Flush buffer, then Tab
      if (buffer) {
        await sendCdpCommand(wsUrl, 'Input.insertText', { text: buffer });
        await settle();  // Let browser process text before Tab
        buffer = '';
      }
      await keyboardPress(tabIndexOrWsUrl, 'Tab');
      await settle();  // Let browser process Tab and update focus
    } else if (char === '\n') {
      // Flush buffer, then Enter (or literal newline in textarea)
      if (buffer) {
        await sendCdpCommand(wsUrl, 'Input.insertText', { text: buffer });
        await settle();  // Let browser process text before Enter
        buffer = '';
      }
      // Re-check if current focus is a textarea (focus may have changed after Tab)
      const currentFocus = await sendCdpCommand(wsUrl, 'Runtime.evaluate', {
        expression: `({ isTextarea: document.activeElement?.tagName === 'TEXTAREA' })`,
        returnByValue: true
      });
      const currentlyInTextarea = currentFocus.result?.value?.isTextarea || false;

      if (currentlyInTextarea) {
        await sendCdpCommand(wsUrl, 'Input.insertText', { text: '\n' });
      } else {
        await keyboardPress(tabIndexOrWsUrl, 'Enter');
      }
      await settle();
    } else {
      buffer += char;
    }
  }

  // Flush remaining buffer
  if (buffer) {
    await sendCdpCommand(wsUrl, 'Input.insertText', { text: buffer });
  }

  return { typed: true, value };
}

// Legacy alias
const insertText = fill;

/**
 * Press a special key using CDP Input.dispatchKeyEvent (JRV-127, JRV-125)
 * Supports: Tab, Enter, Escape, Arrow keys, F1-F12, etc.
 */
async function keyboardPress(tabIndexOrWsUrl, keyName, modifiers = {}) {
  const wsUrl = await resolveWsUrl(tabIndexOrWsUrl);

  const keyDef = KEY_DEFINITIONS[keyName];
  if (!keyDef) {
    throw new Error(`Unknown key: ${keyName}. Supported keys: ${Object.keys(KEY_DEFINITIONS).join(', ')}`);
  }

  // Calculate modifier flags
  let modifierFlags = 0;
  if (modifiers.alt) modifierFlags |= 1;
  if (modifiers.ctrl) modifierFlags |= 2;
  if (modifiers.meta) modifierFlags |= 4;
  if (modifiers.shift) modifierFlags |= 8;

  // Send keyDown
  await sendCdpCommand(wsUrl, 'Input.dispatchKeyEvent', {
    type: 'keyDown',
    key: keyDef.key,
    code: keyDef.code,
    windowsVirtualKeyCode: keyDef.keyCode,
    nativeVirtualKeyCode: keyDef.keyCode,
    modifiers: modifierFlags
  });

  // Send keyUp
  a

... [Content truncated, total 62,931 chars] ...