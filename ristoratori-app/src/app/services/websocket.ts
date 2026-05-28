import { Injectable, OnDestroy } from '@angular/core';
import { Subject } from 'rxjs';
import { io, Socket } from 'socket.io-client';
import { AuthService } from './auth';

const WS_URL = '/ristoratore';

@Injectable({ providedIn: 'root' })
export class WebsocketService implements OnDestroy {

  private socket!: Socket;
  private idRistorante: number | null = null;
  nuovoOrdine$ = new Subject<any>();
  ordineAccettato$ = new Subject<any>();
  ordineRifiutato$ = new Subject<any>();
  ordineAnnullato$ = new Subject<any>();
  ordineAssegnato$ = new Subject<any>();

  constructor(private auth: AuthService) {}

  connect(idRistorante: number): void {
    if (this.idRistorante === idRistorante && this.socket?.connected) return;
    if (this.socket) this.socket.disconnect();

    this.idRistorante = idRistorante;
    this.socket = io(WS_URL, {
      query: { token: this.auth.getToken(), id_ristorante: idRistorante },
      transports: ['polling', 'websocket'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 3000
    });

    this.socket.on('connect', () => console.log('WS connesso:', this.socket.id));
    this.socket.on('connect_error', (err: any) => console.error('WS errore:', err.message));
    this.socket.on('disconnect', (reason: string) => console.log('WS disconnesso:', reason));

    this.socket.on('nuovo_ordine', (data: any) => this.nuovoOrdine$.next(data));
    this.socket.on('ordine_accettato', (data: any) => this.ordineAccettato$.next(data));
    this.socket.on('ordine_rifiutato', (data: any) => this.ordineRifiutato$.next(data));
    this.socket.on('ordine_annullato', (data: any) => this.ordineAnnullato$.next(data));
    this.socket.on('ordine_assegnato', (data: any) => this.ordineAssegnato$.next(data));
  }

  disconnect(): void {
    this.idRistorante = null;
    this.socket?.disconnect();
  }

  ngOnDestroy(): void { this.disconnect(); }
}
