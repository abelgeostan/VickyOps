type EventCallback = (data: any) => void;

class WebSocketClient {
  private socket: WebSocket | null = null;
  private listeners: Map<string, Set<EventCallback>> = new Map();
  private reconnectInterval = 3000;
  private isConnecting = false;

  constructor() {
    this.connect();
  }

  private connect() {
    if (this.isConnecting || (this.socket && this.socket.readyState === WebSocket.OPEN)) {
      return;
    }
    this.isConnecting = true;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        this.isConnecting = false;
        // Keep alive ping
        this.emit('connection', { connected: true });
      };

      this.socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const eventType = payload.event;
          if (eventType && this.listeners.has(eventType)) {
            this.listeners.get(eventType)?.forEach((cb) => cb(payload.data));
          }
          // Global wild-card listeners
          if (this.listeners.has('*')) {
            this.listeners.get('*')?.forEach((cb) => cb(payload));
          }
        } catch (e) {
          // ignore non-json ping/pong
        }
      };

      this.socket.onclose = () => {
        this.isConnecting = false;
        this.emit('connection', { connected: false });
        setTimeout(() => this.connect(), this.reconnectInterval);
      };

      this.socket.onerror = () => {
        this.isConnecting = false;
        try {
          this.socket?.close();
        } catch (_) {}
      };
    } catch (e) {
      this.isConnecting = false;
      setTimeout(() => this.connect(), this.reconnectInterval);
    }
  }

  public on(event: string, callback: EventCallback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)?.add(callback);
    return () => this.off(event, callback);
  }

  public off(event: string, callback: EventCallback) {
    this.listeners.get(event)?.delete(callback);
  }

  private emit(event: string, data: any) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)?.forEach((cb) => cb(data));
    }
  }
}

export const wsClient = new WebSocketClient();
