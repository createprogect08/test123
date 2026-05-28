import { inject } from '@angular/core';
import { CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth';
export const authGuard: CanActivateFn = () => {
  // Salva token da URL se presente (primo accesso dopo redirect)
  const params = new URLSearchParams(window.location.search);
  const token  = params.get('token');
  const nome   = params.get('nome');
  const id     = params.get('id');
  const tipo   = params.get('tipo');
  if (token && tipo === 'rider') {
    localStorage.setItem('marisa_token', token);
    localStorage.setItem('marisa_user', JSON.stringify({
      id:   Number(id),
      nome: nome || '',
      tipo: 'rider'
    }));
    window.history.replaceState({}, '', window.location.pathname);
  }

  const auth = inject(AuthService);
  if (auth.isLoggedIn()) {
    const utente = auth.getUtente();
    if (utente?.tipo === 'rider') return true;
  }
  window.location.href = 'https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev';
  return false;
};
