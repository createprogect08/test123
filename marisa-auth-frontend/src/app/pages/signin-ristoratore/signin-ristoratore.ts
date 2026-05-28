import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { AuthService } from '../../services/auth';
import { GeocodingService, GeoResult } from '../../services/geocoding';

@Component({
  selector: 'app-signin-ristoratore',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './signin-ristoratore.html',
  styleUrl: './signin-ristoratore.css'
})
export class SigninRistoratoreComponent implements OnInit, OnDestroy {
  nome = '';
  email = '';
  telefono = '';
  password = '';
  confermaPassword = '';
  nomeRistorante = '';
  via = '';
  partitaIva = '';
  telefonoRistorante = '';
  loading = false;
  error = '';
  showPassword = false;

  lat: number | null = null;
  lng: number | null = null;
  suggerimenti: GeoResult[] = [];
  mostraSuggerimenti = false;
  private search$ = new Subject<string>();
  private subs: Subscription[] = [];

  constructor(
    private auth: AuthService,
    private router: Router,
    private geo: GeocodingService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.subs.push(
      this.search$.pipe(
        debounceTime(350),
        distinctUntilChanged(),
        switchMap(q => this.geo.suggest(q))
      ).subscribe(results => {
        this.suggerimenti = results;
        this.mostraSuggerimenti = results.length > 0;
        this.cdr.detectChanges();
      })
    );
  }

  onViaInput(): void {
    this.lat = null;
    this.lng = null;
    if (this.via.length >= 3) this.search$.next(this.via);
    else { this.suggerimenti = []; this.mostraSuggerimenti = false; }
  }

  seleziona(r: GeoResult): void {
    this.via = r.shortName;
    this.lat = r.lat;
    this.lng = r.lng;
    this.mostraSuggerimenti = false;
    this.suggerimenti = [];
    this.error = '';
    this.cdr.detectChanges();
  }

  chiudiSuggerimenti(): void {
    setTimeout(() => { this.mostraSuggerimenti = false; this.cdr.detectChanges(); }, 200);
  }

  registrati() {
    if (!this.nome || !this.email || !this.password || !this.confermaPassword ||
        !this.nomeRistorante || !this.via) {
      this.error = 'Compila tutti i campi obbligatori.'; return;
    }
    if (this.password !== this.confermaPassword) {
      this.error = 'Le password non coincidono.'; return;
    }
    if (this.password.length < 6) {
      this.error = 'La password deve essere di almeno 6 caratteri.'; return;
    }
    if (this.lat === null || this.lng === null) {
      this.error = 'Seleziona un indirizzo dalla lista dei suggerimenti.'; return;
    }

    this.loading = true;
    this.error = '';

    this.auth.registerRistoratore({
      nome: this.nome,
      email: this.email,
      password: this.password,
      telefono: this.telefono || undefined,
      nome_ristorante: this.nomeRistorante,
      via: this.via,
      lat: this.lat,
      lng: this.lng,
      partita_iva: this.partitaIva || undefined,
      telefono_ristorante: this.telefonoRistorante || undefined,
    }).subscribe({
      next: (res) => {
        this.loading = false;
        this.auth.saveSession(res.token, res.tipo || 'ristoratore');
        this.auth.redirect(res.redirect_url);
      },
      error: (err) => {
        this.loading = false;
        if (err.status === 409) this.error = 'Email già registrata.';
        else if (err.status === 422) this.error = 'Email non valida.';
        else this.error = 'Errore di connessione. Riprova.';
      }
    });
  }

  torna() { this.router.navigate(['/']); }
  ngOnDestroy(): void { this.subs.forEach(s => s.unsubscribe()); }
}
