import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth';

const API = '/rider';

@Injectable({ providedIn: 'root' })
export class RiderService {

  constructor(private http: HttpClient, private auth: AuthService) {}

  private headers(): HttpHeaders {
    return new HttpHeaders({ Authorization: `Bearer ${this.auth.getToken()}` });
  }

  getMe(): Observable<any> {
    return this.http.get(`${API}/rider/me`, { headers: this.headers() });
  }

  updateMe(dati: FormData): Observable<any> {
    return this.http.put(`${API}/rider/me`, dati, { headers: this.headers() });
  }

  getOrdiniDisponibili(): Observable<any> {
    return this.http.get(`${API}/rider/ordini/disponibili`, { headers: this.headers() });
  }

  getMieiOrdini(): Observable<any> {
    return this.http.get(`${API}/rider/ordini/miei`, { headers: this.headers() });
  }

  accettaOrdine(idOrdine: number): Observable<any> {
    return this.http.post(`${API}/rider/ordini/${idOrdine}/accetta`, {}, { headers: this.headers() });
  }

  rifiutaOrdine(idOrdine: number): Observable<any> {
    return this.http.post(`${API}/rider/ordini/${idOrdine}/rifiuta`, {}, { headers: this.headers() });
  }

  aggiornaPostura(lat: number, lng: number): Observable<any> {
    return this.http.post(`${API}/rider/posizione`, { lat, lng }, { headers: this.headers() });
  }

  segnaInConsegna(idOrdine: number): Observable<any> {
    return this.http.post(`${API}/rider/ordini/${idOrdine}/accetta`, {}, { headers: this.headers() });
  }

  segnaSottoCasa(idOrdine: number): Observable<any> {
    return this.http.post(`${API}/rider/ordini/${idOrdine}/sotto_casa`, {}, { headers: this.headers() });
  }

  segnaConsegnato(idOrdine: number, token: string): Observable<any> {
    return this.http.post(`${API}/rider/ordini/${idOrdine}/consegnato`, { token }, { headers: this.headers() });
  }
}
