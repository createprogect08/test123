import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

const AUTH_URL = '';

export interface CheckEmailResponse {
  registrato: boolean;
  tipo?: string;
}

export interface AuthResponse {
  token: string;
  redirect_url: string;
  id?: number;
  nome?: string;
  tipo?: string;
  messaggio?: string;
  crediti?: number;
}

export interface VerifyResponse {
  valido: boolean;
  utente?: {
    id: number;
    nome: string;
    email: string;
    tipo: string;
    crediti?: number;
  };
  redirect_url?: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {

  constructor(private http: HttpClient) {}

  checkEmail(email: string): Observable<CheckEmailResponse> {
    return this.http.post<CheckEmailResponse>(`${AUTH_URL}/auth/check-email`, { email });
  }

  login(email: string, password: string): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${AUTH_URL}/auth/login`, { email, password });
  }

  registerUtente(data: {
    nome: string; email: string; password: string; telefono?: string;
  }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${AUTH_URL}/auth/register/utente`, data);
  }

  registerRider(data: {
    nome: string; cognome: string; email: string; password: string;
    telefono?: string; codice_fiscale: string; zona?: string;
  }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${AUTH_URL}/auth/register/rider`, data);
  }

  registerRistoratore(data: {
    nome: string; email: string; password: string; telefono?: string;
    nome_ristorante: string; via: string; lat: number; lng: number;
    partita_iva?: string; telefono_ristorante?: string;
  }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${AUTH_URL}/auth/register/ristoratore`, data);
  }

  verify(): Observable<VerifyResponse> {
    return this.http.get<VerifyResponse>(`${AUTH_URL}/auth/verify`);
  }

  logout(): Observable<any> {
    return this.http.post(`${AUTH_URL}/auth/logout`, {});
  }

  // Salva token + marisa_user compatibile con tutti i frontend
  saveSession(token: string, tipo: string, res?: AuthResponse): void {
    localStorage.setItem('marisa_token', token);
    localStorage.setItem('marisa_tipo',  tipo);
    if (res) {
      localStorage.setItem('marisa_user', JSON.stringify({
        id:   res.id,
        nome: res.nome,
        tipo: res.tipo,
        crediti: res.crediti ?? 0
      }));
    }
  }

  getToken(): string | null { return localStorage.getItem('marisa_token'); }
  getTipo():  string | null { return localStorage.getItem('marisa_tipo');  }

  clearSession(): void {
    localStorage.removeItem('marisa_token');
    localStorage.removeItem('marisa_tipo');
    localStorage.removeItem('marisa_user');
  }

  isLoggedIn(): boolean { return !!this.getToken(); }

  redirect(url: string): void { window.location.href = url; }
}
