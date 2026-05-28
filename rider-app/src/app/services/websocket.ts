import { Injectable, OnDestroy, NgZone } from '@angular/core';
import { Subject } from 'rxjs';
import { io, Socket } from 'socket.io-client';
import { AuthService } from './auth';

const WS_URL = '/rider';

@Injectable({ providedIn: 'root' })
export class WebsocketService implements OnDestroy {

  private socket: Socket | null = null;

  nuovaConsegna$   = new Subject<any>();
  ordineAssegnato$ = new Subject<any>();
  riderPosizione$  = new Subject<any>();

  constructor(private auth: AuthService, private zone: NgZone) {}

  connect(): void {
    if (this.socket?.connected) return;

    const token = this.auth.getToken();

    this.socket = io(WS_URL, {
      query         : { token },
      transports    : ['websocket', 'polling'],
      reconnection  : true,
      reconnectionDelay: 2000
    });

    this.socket.on('connect', () => {
      console.log('WS connesso:', this.socket?.id);
    });

    this.socket.on('connect_error', err => {
      console.warn('WS errore connessione:', err.message);
    });

    this.socket.on('nuova_consegna', (data: any) => {
      console.log('Nuova consegna ricevuta:', data);
      this.nuovaConsegna$.next(data);
    });

    this.socket.on('ordine_assegnato', (data: any) => {
      this.ordineAssegnato$.next(data);
    });

    this.socket.on('rider_posizione', (data: any) => {
      this.riderPosizione$.next(data);
    });

    this.socket.on('disconnect', () => {
      console.log('WS disconnesso');
    });
  }

  joinOrdine(idOrdine: number): void {
    this.socket?.emit('join_ordine', { id_ordine: idOrdine });
  }

  leaveOrdine(idOrdine: number): void {
    this.socket?.emit('leave_ordine', { id_ordine: idOrdine });
  }

  disconnect(): void {
    this.socket?.disconnect();
    this.socket = null;
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  ngOnDestroy(): void {
    this.disconnect();
  }
}
