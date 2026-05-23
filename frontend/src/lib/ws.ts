import type { WsEvent } from "@/types/api";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

type WsListener = (event: WsEvent) => void;

export class SimulationWebSocket {
  private ws: WebSocket | null = null;
  private listeners: Set<WsListener> = new Set();
  private reconnectDelay = 1000;
  private _simId: string;
  private _closed = false;

  constructor(simId: string) {
    this._simId = simId;
  }

  connect(): void {
    this._closed = false;
    this.ws = new WebSocket(`${WS_BASE}/ws/simulations/${this._simId}`);

    this.ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as WsEvent;
        this.listeners.forEach((l) => l(event));
      } catch {}
    };

    this.ws.onclose = () => {
      if (!this._closed) {
        setTimeout(() => this.connect(), this.reconnectDelay);
        this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 10000);
      }
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
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
