import { ApplicationConfig, APP_INITIALIZER } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { routes } from './app.routes';

function initApp(): () => void {
  return () => {
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
      window.history.replaceState({}, '', '/');
    }
  };
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes),
    provideHttpClient(),
    {
      provide: APP_INITIALIZER,
      useFactory: initApp,
      multi: true
    }
  ]
};
