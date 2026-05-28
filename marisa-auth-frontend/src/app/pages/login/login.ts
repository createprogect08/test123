import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent implements OnInit {
  email       = '';
  password    = '';
  loading     = false;
  error       = '';
  showPassword = false;

  constructor(private auth: AuthService, private router: Router) {}

  ngOnInit() {
    const nav = window.history.state;
    if (nav?.email) this.email = nav.email;
  }

  accedi() {
    if (!this.password) { this.error = 'Inserisci la password.'; return; }
    this.loading = true;
    this.error   = '';

    this.auth.login(this.email, this.password).subscribe({
      next: (res) => {
        this.loading = false;
        this.auth.saveSession(res.token, res.tipo || '', res);
        this.auth.redirect(res.redirect_url);
      },
      error: (err) => {
        this.loading = false;
        this.error = err.status === 401
          ? 'Password non corretta.'
          : 'Errore di connessione. Riprova.';
      }
    });
  }

  torna() { this.router.navigate(['/']); }
}
