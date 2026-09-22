// Server settings. Environment overrides for the server PC; defaults suit a LAN.
export const PORT = Number(process.env.PORT || 8080);            // HTTP + WebSocket
export const UDP_PORT = Number(process.env.UDP_PORT || 5005);    // band frames arrive here
export const DATA_DIR = process.env.DATA_DIR || new URL('../data/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
export const POLL_MS = 2000;                                     // device /status polling
export const RING_SIZE = 3000;                                   // 60 s of 50 Hz frames kept in memory
export const DEVICE_TIMEOUT_MS = 1500;                           // per HTTP call to a device
