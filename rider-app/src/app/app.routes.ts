import { Routes } from '@angular/router';
import { authGuard } from './guards/auth-guard';

export const routes: Routes = [
  {
    path: 'do-login',
    loadComponent: () => import('./pages/do-login/do-login').then(m => m.DoLogin)
  },
  {
    path: '',
    loadComponent: () => import('./pages/home/home').then(m => m.Home),
    canActivate: [authGuard]
  },
  {
    path: 'consegna/:idOrdine',
    loadComponent: () => import('./pages/mappa/mappa').then(m => m.Mappa),
    canActivate: [authGuard]
  },
  {
    path: 'setting',
    loadComponent: () => import('./pages/setting/setting').then(m => m.Setting),
    canActivate: [authGuard]
  },
  { path: '**', redirectTo: '' }
];
