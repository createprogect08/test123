import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

const API = '/api';

export interface Ristorante {
  distanza_km?: number;
  id: number;
  nome: string;
  descrizione: string;
  via: string;
  lat: number;
  lng: number;
  categoria: string;
  foto_profilo?: string;
}

export interface MenuItem {
  id: number;
  nome: string;
  descrizione: string;
  prezzo: number;
  foto?: string;
  categoria?: string;
  disponibile: boolean;
}

@Injectable({ providedIn: 'root' })
export class RestaurantService {
  constructor(private http: HttpClient) {}

  getVicini(lat: number, lng: number, raggio = 30000): Observable<Ristorante[]> {
    return this.http.get<Ristorante[]>(
      `${API}/ristoranti/vicini?lat=${lat}&lng=${lng}&raggio=${raggio}`
    );
  }

  getRistorante(id: number): Observable<Ristorante> {
    return this.http.get<Ristorante>(`${API}/ristoranti/${id}`);
  }

  getMenu(idRistorante: number): Observable<MenuItem[]> {
    return this.http.get<MenuItem[]>(`${API}/menu/${idRistorante}/items`);
  }
}
