import { Injectable } from '@angular/core';

export interface Utente {
  id: number;
  nome: string;
  email: string;
  tipo: string;
  foto_profilo?: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {

  private readonly TOKEN_KEY  = 'marisa_token';
  private readonly UTENTE_KEY = 'marisa_user';

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getUtente(): Utente | null {
    try {
      const raw = localStorage.getItem(this.UTENTE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  isLoggedIn(): boolean {
    return !!this.getToken() && !!this.getUtente();
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.UTENTE_KEY);
    window.location.href = 'https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev';
  }
}
