import { Injectable, OnDestroy } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { io, Socket } from 'socket.io-client';

@Injectable({ providedIn: 'root' })
export class WebsocketService implements OnDestroy {
  private sockets: Map<string, Socket> = new Map();

  connect(url: string): Socket {
    if (this.sockets.has(url)) return this.sockets.get(url)!;
    const token = localStorage.getItem('marisa_token');
    const socket = io(url, {
      auth: { token },
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 2000
    });
    this.sockets.set(url, socket);
    return socket;
  }

  on<T>(url: string, event: string): Observable<T> {
    const socket = this.connect(url);
    return new Observable<T>(observer => {
      socket.on(event, (data: T) => observer.next(data));
      return () => socket.off(event);
    });
  }

  emit(url: string, event: string, data: any): void {
    const socket = this.connect(url);
    socket.emit(event, data);
  }

  disconnect(url: string): void {
    const socket = this.sockets.get(url);
    if (socket) {
      socket.disconnect();
      this.sockets.delete(url);
    }
  }

  disconnectAll(): void {
    this.sockets.forEach(s => s.disconnect());
    this.sockets.clear();
  }

  ngOnDestroy(): void {
    this.disconnectAll();
  }
}
