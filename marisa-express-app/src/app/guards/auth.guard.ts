import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(private router: Router) {}

  canActivate(): boolean {
    const token = localStorage.getItem('marisa_token');
    if (token) return true;
    window.location.href = 'https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev';
    return false;
  }
}
