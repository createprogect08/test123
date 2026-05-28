import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { Header } from './components/header/header';
import { AuthService } from './services/auth';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, Header],
  template: `
    <app-header />
    <main class="main-content">
      <router-outlet />
    </main>
  `,
  styles: [`
    .main-content {
      margin-top: 64px;
      padding: 24px;
      max-width: 1200px;
      margin-left: auto;
      margin-right: auto;
    }
  `]
})
export class App implements OnInit {
  constructor(private auth: AuthService) {}

  ngOnInit(): void {
    // Leggi token da URL se presente (redirect da auth frontend)
    const params = new URLSearchParams(window.location.search);
    const token  = params.get('token');
    const nome   = params.get('nome');
    const id     = params.get('id');
    const tipo   = params.get('tipo');

    if (token && tipo === 'ristoratore') {
      this.auth.setToken(token, {
        id:   Number(id),
        nome: nome || '',
        tipo: tipo
      });
      // Rimuovi params dall'URL senza reload
      window.history.replaceState({}, '', '/');
    }
  }
}
