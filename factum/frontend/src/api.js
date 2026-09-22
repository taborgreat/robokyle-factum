// Thin client for the backend. Every call returns parsed JSON or throws an Error with the server's message.
export async function api(method, route, body) {
  const res = await fetch(route, { method, headers: { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body) });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.error || `${res.status}`);
  return json;
}
export const get = r => api('GET', r);
export const post = (r, b) => api('POST', r, b);
export const put = (r, b) => api('PUT', r, b);

// Live feed: frames and device status over the WebSocket, with reconnect.
export function connect(onMessage) {
  let ws, closed = false, timer;
  const open = () => {
    ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`);
    ws.onmessage = e => onMessage(JSON.parse(e.data));
    ws.onclose = () => { if (!closed) timer = setTimeout(open, 1500); };
  };
  open();
  return () => { closed = true; clearTimeout(timer); ws?.close(); };
}
