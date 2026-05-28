import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-signin-utente',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './signin-utente.html',
  styleUrl: './signin-utente.css'
})
export class SigninUtenteComponent implements OnInit {
  email = '';
  nome = '';
  telefono = '';
  password = '';
  confermaPassword = '';
  loading = false;
  error = '';
  showPassword = false;

  constructor(private auth: AuthService, private router: Router) {}

  ngOnInit() {
    const nav = window.history.state;
    if (nav?.email) this.email = nav.email;
  }

  registrati() {
    if (!this.nome || !this.email || !this.password || !this.confermaPassword) {
      this.error = 'Compila tutti i campi obbligatori.';
      return;
    }
    if (this.password !== this.confermaPassword) {
      this.error = 'Le password non coincidono.';
      return;
    }
    if (this.password.length < 6) {
      this.error = 'La password deve essere di almeno 6 caratteri.';
      return;
    }

    this.loading = true;
    this.error = '';

    this.auth.registerUtente({
      nome: this.nome,
      email: this.email,
      password: this.password,
      telefono: this.telefono || undefined
    }).subscribe({
      next: (res) => {
        this.loading = false;
        this.auth.saveSession(res.token, res.tipo || 'utente');
        this.auth.redirect(res.redirect_url);
      },
      error: (err) => {
        this.loading = false;
        if (err.status === 409) {
          this.error = 'Email già registrata.';
        } else if (err.status === 422) {
          this.error = 'Email non valida.';
        } else {
          this.error = 'Errore di connessione. Riprova.';
        }
      }
    });
  }

  torna() {
    this.router.navigate(['/']);
  }
}
