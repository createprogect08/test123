import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

const API = '/api';

export interface OrdinePayload {
  id_ristorante: number;
  items: { id_menu_item: number; quantita: number }[];
  indirizzo_consegna: string;
  lat_consegna: number;
  lng_consegna: number;
  metodo_pagamento: 'crediti' | 'stripe';
}

export interface Ordine {
  id: number;
  stato: string;
  items: any[];
  totale: number;
  id_rider?: number;
  token_consegna?: string;
  created_at?: string;
  nome_ristorante?: string;
}

@Injectable({ providedIn: 'root' })
export class OrderService {
  constructor(private http: HttpClient) {}

  creaOrdine(payload: OrdinePayload): Observable<{ id: number; stripe_url?: string }> {
    return this.http.post<{ id: number }>(`${API}/ordini`, payload);
  }

  getOrdine(id: number): Observable<Ordine> {
    return this.http.get<Ordine>(`${API}/ordini/${id}`);
  }

  getOrdini(): Observable<Ordine[]> {
    return this.http.get<any>(`${API}/ordini`).pipe(
      map((r: any) => Array.isArray(r) ? r : (r.ordini || []))
    );
  }

  getSaldo(): Observable<{ saldo: number }> {
    return this.http.get<{ saldo: number }>(`${API}/wallet/saldo`);
  }

  verificaRicarica(sessionId: string): Observable<any> {
    return this.http.post(`${API}/wallet/verifica-ricarica`, { session_id: sessionId });
  }

  ricaricaStripe(importo: number): Observable<any> {
    return this.http.post(`${API}/wallet/ricarica-stripe`, { importo });
  }

  ricaricaWallet(importo: number, metodo: string): Observable<any> {
    return this.http.post(`${API}/wallet/ricarica`, { importo, metodo });
  }

  getTransazioni(): Observable<any[]> {
    return this.http.get<any>(`${API}/wallet/transazioni`).pipe(
      map((r: any) => Array.isArray(r) ? r : (r.transazioni || []))
    );
  }

  getRiderPosizione(id_rider: number): Observable<{ lat: number; lng: number; updated_at: string }> {
    return this.http.get<any>(`${API}/rider/posizione/${id_rider}`);
  }


  confermaTokenConsegna(id: number, token: string): Observable<any> {
    return this.http.post(`${API}/ordini/${id}/conferma_token`, { token });
  }

  annullaOrdine(id: number): Observable<any> {
    return this.http.delete(`${API}/ordini/${id}`);
  }
}
// patch
