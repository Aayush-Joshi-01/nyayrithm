import type { WsEvent } from "@/types/api";
import { getAccessToken } from "@/lib/auth-token";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

type WsListener = (event: WsEvent) => void;

export class SimulationWebSocket {
  private ws: WebSocket | null = null;
  private listeners: Set<WsListener> = new Set();
  private reconnectDelay = 1000;
  private _simId: string;
  private _closed = false;
  private _connecting = false;
  private _authRetries = 0;

  constructor(simId: string) {
    this._simId = simId;
  }

  connect(): void {
    this._closed = false;

    // Don't stack sockets — a CONNECTING/OPEN socket is already (re)connecting.
    const rs = this.ws?.readyState;
    if (rs === WebSocket.CONNECTING || rs === WebSocket.OPEN) return;

    if (this._connecting) return;
    this._connecting = true;
    void this.open();
  }

  private async open(forceRefresh = false): Promise<void> {
    // Browsers can't set headers on a WebSocket, so the token rides in the query string.
    const token = await getAccessToken(forceRefresh);
    this._connecting = false;
    if (this._closed) return;
    const qs = token ? `?token=${encodeURIComponent(token)}` : "";
    this.ws = new WebSocket(`${WS_BASE}/ws/simulations/${this._simId}${qs}`);

    this.ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as WsEvent;
        this.listeners.forEach((l) => l(event));
      } catch {}
    };

    this.ws.onclose = (e) => {
      // 4401 = token rejected, 4403 = not your simulation. Retrying a 4403 is futile.
      if (e.code === 4403) return;
      if (e.code === 4401) {
        // One forced token refresh, then give up rather than hammer the server.
        if (this._authRetries++ < 1) void this.open(true);
        return;
      }
      if (!this._closed) {
        setTimeout(() => this.connect(), this.reconnectDelay);
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 10000);
      }
    };

    // Let onclose drive reconnection; closing here would just double it up.
    this.ws.onerror = () => {};

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
      this._authRetries = 0;
    };
  }

  on(listener: WsListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  send(msg: object): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  disconnect(): void {
    this._closed = true;
    this.ws?.close();
    this.listeners.clear();
  }
}
