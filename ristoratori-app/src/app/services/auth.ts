import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class AuthService {

  private readonly TOKEN_KEY = 'marisa_token';
  private readonly USER_KEY  = 'marisa_user';

  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getUser(): any {
    const u = localStorage.getItem(this.USER_KEY);
    return u ? JSON.parse(u) : null;
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    if (!token) return false;

    try {
      // Decodifica payload JWT (senza verifica firma — la verifica la fa il backend)
      const payload = JSON.parse(atob(token.split('.')[1]));
      const now     = Math.floor(Date.now() / 1000);

      if (payload.exp && payload.exp < now) {
        this.logout();
        return false;
      }

      if (payload.tipo !== 'ristoratore') {
        this.logout();
        return false;
      }

      return true;
    } catch {
      this.logout();
      return false;
    }
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  // Usato per test — salva token manualmente
  setToken(token: string, user: any): void {
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }
}
