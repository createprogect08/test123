import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-email-check',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './email-check.html',
  styleUrl: './email-check.css'
})
export class EmailCheckComponent {
  email = '';
  loading = false;
  error = '';

  constructor(private auth: AuthService, private router: Router) {}

  continua() {
    if (!this.email || !this.email.includes('@')) {
      this.error = 'Inserisci un indirizzo email valido.';
      return;
    }

    this.loading = true;
    this.error = '';

    this.auth.checkEmail(this.email).subscribe({
      next: (res) => {
        this.loading = false;
        if (res.registrato) {
          this.router.navigate(['/login'], { state: { email: this.email } });
        } else {
          this.router.navigate(['/signin'], { state: { email: this.email } });
        }
      },
      error: () => {
        this.loading = false;
        this.error = 'Errore di connessione. Riprova.';
      }
    });
  }

  goToRider() {
    this.router.navigate(['/signin/rider']);
  }

  goToRistoratore() {
    this.router.navigate(['/signin/ristoratore']);
  }
}
