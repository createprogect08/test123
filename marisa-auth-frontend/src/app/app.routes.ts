import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./pages/email-check/email-check').then(m => m.EmailCheckComponent),
  },
  {
    path: 'login',
    loadComponent: () =>
      import('./pages/login/login').then(m => m.LoginComponent),
  },
  {
    path: 'signin',
    loadComponent: () =>
      import('./pages/signin-utente/signin-utente').then(m => m.SigninUtenteComponent),
  },
  {
    path: 'signin/rider',
    loadComponent: () =>
      import('./pages/signin-rider/signin-rider').then(m => m.SigninRiderComponent),
  },
  {
    path: 'signin/ristoratore',
    loadComponent: () =>
      import('./pages/signin-ristoratore/signin-ristoratore').then(m => m.SigninRistoratoreComponent),
  },
  {
    path: '**',
    redirectTo: '',
  },
];
