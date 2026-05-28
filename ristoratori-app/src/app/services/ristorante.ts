import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth';

const API = '/ristoratore';

@Injectable({ providedIn: 'root' })
export class RistoranteService {

  constructor(private http: HttpClient, private auth: AuthService) {}

  private headers(): HttpHeaders {
    return new HttpHeaders({ Authorization: `Bearer ${this.auth.getToken()}` });
  }

  // Header senza Content-Type per FormData (lo imposta il browser)
  private headersFormData(): HttpHeaders {
    return new HttpHeaders({ Authorization: `Bearer ${this.auth.getToken()}` });
  }

  // ── ME ────────────────────────────────────────────────────────────────────
  getMe(): Observable<any> {
    return this.http.get(`${API}/ristoratore/me`, { headers: this.headers() });
  }

  updateMe(formData: FormData): Observable<any> {
    return this.http.put(`${API}/ristoratore/me`, formData, { headers: this.headersFormData() });
  }

  // ── ORDINI ────────────────────────────────────────────────────────────────
  getOrdini(stato?: string): Observable<any> {
    const params = stato ? `?stato=${stato}` : '';
    return this.http.get(`${API}/ristoratore/ordini${params}`, { headers: this.headers() });
  }

  getOrdine(id: number): Observable<any> {
    return this.http.get(`${API}/ristoratore/ordini/${id}`, { headers: this.headers() });
  }

  accettaOrdine(id: number): Observable<any> {
    return this.http.post(`${API}/ristoratore/ordini/${id}/accetta`, {}, { headers: this.headers() });
  }

  rifiutaOrdine(id: number, motivo: string): Observable<any> {
    return this.http.post(`${API}/ristoratore/ordini/${id}/rifiuta`, { motivo }, { headers: this.headers() });
  }

  segnalaRitirato(id: number): Observable<any> {
    return this.http.post(`${API}/ristoratore/ordini/${id}/ritirato`, {}, { headers: this.headers() });
  }

  // ── MENU ──────────────────────────────────────────────────────────────────
  getMenu(): Observable<any> {
    return this.http.get(`${API}/ristoratore/menu`, { headers: this.headers() });
  }

  creaItem(item: any): Observable<any> {
    return this.http.post(`${API}/ristoratore/menu`, item, { headers: this.headers() });
  }

  creaItemFormData(fd: FormData): Observable<any> {
    return this.http.post(`${API}/ristoratore/menu`, fd, { headers: this.headersFormData() });
  }

  modificaItem(id: number, item: any): Observable<any> {
    return this.http.put(`${API}/ristoratore/menu/${id}`, item, { headers: this.headers() });
  }

  modificaItemFormData(id: number, fd: FormData): Observable<any> {
    return this.http.put(`${API}/ristoratore/menu/${id}`, fd, { headers: this.headersFormData() });
  }

  eliminaItem(id: number): Observable<any> {
    return this.http.delete(`${API}/ristoratore/menu/${id}`, { headers: this.headers() });
  }
}
