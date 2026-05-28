import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { AuthService } from '../../services/auth';
import { GeocodingService, GeoResult } from '../../services/geocoding';

@Component({
  selector: 'app-signin-rider',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './signin-rider.html',
  styleUrl: './signin-rider.css'
})
export class SigninRiderComponent implements OnInit, OnDestroy {
  nome = '';
  cognome = '';
  email = '';
  telefono = '';
  codiceFiscale = '';
  zona = '';
  password = '';
  confermaPassword = '';
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

  onZonaInput(): void {
    this.lat = null;
    this.lng = null;
    if (this.zona.length >= 3) this.search$.next(this.zona);
    else { this.suggerimenti = []; this.mostraSuggerimenti = false; }
  }

  seleziona(r: GeoResult): void {
    this.zona = r.shortName;
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
    if (!this.nome || !this.cognome || !this.email || !this.password || !this.codiceFiscale) {
      this.error = 'Compila tutti i campi obbligatori.'; return;
    }
    if (this.password !== this.confermaPassword) {
      this.error = 'Le password non coincidono.'; return;
    }
    if (this.password.length < 6) {
      this.error = 'La password deve essere di almeno 6 caratteri.'; return;
    }
    if (this.codiceFiscale.length !== 16) {
      this.error = 'Il codice fiscale deve essere di 16 caratteri.'; return;
    }

    this.loading = true;
    this.error = '';

    this.auth.registerRider({
      nome: this.nome,
      cognome: this.cognome,
      email: this.email,
      password: this.password,
      telefono: this.telefono || undefined,
      codice_fiscale: this.codiceFiscale.toUpperCase(),
      zona: this.zona || undefined
    }).subscribe({
      next: (res) => {
        this.loading = false;
        this.auth.saveSession(res.token, res.tipo || 'rider');
        this.auth.redirect(res.redirect_url);
      },
      error: (err) => {
        this.loading = false;
        if (err.status === 409) this.error = 'Email o codice fiscale già registrati.';
        else if (err.status === 422) this.error = 'Email non valida.';
        else this.error = 'Errore di connessione. Riprova.';
      }
    });
  }

  torna() { this.router.navigate(['/']); }
  ngOnDestroy(): void { this.subs.forEach(s => s.unsubscribe()); }
}
