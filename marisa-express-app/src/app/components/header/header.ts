import { Component, OnInit, HostListener } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { CartService } from '../../services/cart.service';
import { filter } from 'rxjs/operators';

const AUTH_API = '/auth';

@Component({
  standalone: false,
  selector: 'app-header',
  templateUrl: './header.html',
  styleUrls: ['./header.scss']
})
export class HeaderComponent implements OnInit {
  isLoggato = false;
  nomeUtente = '';
  scrolled = false;
  menuOpen = false;

  constructor(
    private http: HttpClient,
    private router: Router,
    public cartService: CartService
  ) {}

  ngOnInit(): void {
    // Leggi subito da localStorage senza aspettare HTTP
    this.aggiornaStatoLocale();

    this.router.events.pipe(
      filter(e => e instanceof NavigationEnd)
    ).subscribe(() => {
      this.menuOpen = false;
      this.aggiornaStatoLocale();
    });

    // Verifica auth in background solo una volta all'avvio
    this.verificaAuthBackground();
  }

  aggiornaStatoLocale(): void {
    const token = localStorage.getItem('marisa_token');
    const nome = localStorage.getItem('marisa_nome');
    this.isLoggato = !!token;
    this.nomeUtente = nome || '';
  }

  verificaAuthBackground(): void {
    const token = localStorage.getItem('marisa_token');
    if (!token) return;
    this.http.get<{ valido: boolean; utente: { nome: string } }>(
      `${AUTH_API}/auth/verify`
    ).subscribe({
      next: (r) => {
        if (!r.valido) {
          localStorage.removeItem('marisa_token');
          localStorage.removeItem('marisa_nome');
          this.isLoggato = false;
          this.nomeUtente = '';
        } else {
          this.isLoggato = true;
          this.nomeUtente = r.utente?.nome || localStorage.getItem('marisa_nome') || '';
          localStorage.setItem('marisa_nome', this.nomeUtente);
        }
      },
      error: () => {}
    });
  }

  @HostListener('window:scroll')
  onScroll(): void {
    this.scrolled = window.scrollY > 10;
  }

  toggleMenu(): void { this.menuOpen = !this.menuOpen; }

  accedi(): void {
    window.location.href = 'https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev';
  }

  logout(): void {
    localStorage.removeItem('marisa_token');
    localStorage.removeItem('marisa_nome');
    localStorage.removeItem('marisa_id');
    localStorage.removeItem('marisa_tipo');
    this.isLoggato = false;
    this.nomeUtente = '';
    this.cartService.clear();
    this.router.navigate(['/']);
  }
}
