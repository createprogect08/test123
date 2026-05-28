import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';

const API = '/api';

@Component({
  standalone: false,
  selector: 'app-setting',
  templateUrl: './setting.html',
  styleUrls: ['./setting.scss']
})
export class SettingComponent {
  nome = '';
  passwordAttuale = '';
  nuovaPassword = '';
  confermaPassword = '';
  nomeSuccesso = '';
  nomeErrore = '';
  pwSuccesso = '';
  pwErrore = '';
  loadingNome = false;
  loadingPw = false;

  constructor(private http: HttpClient, private router: Router) {}

  salvaNome(): void {
    if (!this.nome.trim()) return;
    this.loadingNome = true;
    this.nomeErrore = '';
    this.nomeSuccesso = '';
    this.http.put(`${API}/utente/nome`, { nome: this.nome }).subscribe({
      next: () => { this.nomeSuccesso = 'Nome aggiornato.'; this.loadingNome = false; },
      error: (e) => { this.nomeErrore = e?.error?.message || 'Errore.'; this.loadingNome = false; }
    });
  }

  cambiaPassword(): void {
    if (this.nuovaPassword !== this.confermaPassword) {
      this.pwErrore = 'Le password non coincidono.';
      return;
    }
    this.loadingPw = true;
    this.pwErrore = '';
    this.pwSuccesso = '';
    this.http.put(`${API}/utente/password`, {
      password_attuale: this.passwordAttuale,
      nuova_password: this.nuovaPassword
    }).subscribe({
      next: () => {
        this.pwSuccesso = 'Password aggiornata.';
        this.loadingPw = false;
        this.passwordAttuale = '';
        this.nuovaPassword = '';
        this.confermaPassword = '';
      },
      error: (e) => { this.pwErrore = e?.error?.message || 'Errore.'; this.loadingPw = false; }
    });
  }

  logout(): void {
    localStorage.removeItem('marisa_token');
    this.router.navigate(['/']);
  }
}
