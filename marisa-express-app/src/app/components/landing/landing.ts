import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { GeocodingService, GeoResult } from '../../services/geocoding.service';

@Component({
  standalone: false,
  selector: 'app-landing',
  templateUrl: './landing.html',
  styleUrls: ['./landing.scss']
})
export class LandingComponent implements OnInit, OnDestroy {
  indirizzo = '';
  loading = false;
  errore = '';
  suggerimenti: GeoResult[] = [];
  mostraSuggerimenti = false;
  private search$ = new Subject<string>();
  private subs: Subscription[] = [];

  constructor(
    private geocoding: GeocodingService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      const token = params['token'];
      if (token) {
        localStorage.setItem('marisa_token', token);
        if (params['nome']) localStorage.setItem('marisa_nome', params['nome']);
        if (params['id'])   localStorage.setItem('marisa_id', params['id']);
        if (params['tipo']) localStorage.setItem('marisa_tipo', params['tipo']);
        const redirect = sessionStorage.getItem('marisa_redirect') || '/';
        sessionStorage.removeItem('marisa_redirect');
        this.router.navigate([redirect], { replaceUrl: true });
      }
    });

    this.indirizzo = sessionStorage.getItem('marisa_address') || '';

    // Autocomplete con debounce
    this.subs.push(
      this.search$.pipe(
        debounceTime(350),
        distinctUntilChanged(),
        switchMap(q => this.geocoding.suggest(q))
      ).subscribe(results => {
        this.suggerimenti = results;
        this.mostraSuggerimenti = results.length > 0;
      })
    );
  }

  onInput(): void {
    if (this.indirizzo.length >= 3) {
      this.search$.next(this.indirizzo);
    } else {
      this.suggerimenti = [];
      this.mostraSuggerimenti = false;
    }
  }

  seleziona(r: GeoResult): void {
    this.indirizzo = r.shortName;
    this.mostraSuggerimenti = false;
    this.suggerimenti = [];
    sessionStorage.setItem('marisa_address', r.shortName);
    sessionStorage.setItem('marisa_lat', r.lat.toString());
    sessionStorage.setItem('marisa_lng', r.lng.toString());
    this.errore = '';
  }

  cerca(): void {
    if (!this.indirizzo.trim()) return;
    // Se ha già coordinate salvate e l'indirizzo corrisponde, vai direttamente
    const savedAddress = sessionStorage.getItem('marisa_address');
    const savedLat = sessionStorage.getItem('marisa_lat');
    const savedLng = sessionStorage.getItem('marisa_lng');
    if (savedLat && savedLng && savedAddress === this.indirizzo) {
      this.router.navigate(['/restaurant']);
      return;
    }

    this.loading = true;
    this.errore = '';
    this.mostraSuggerimenti = false;

    this.geocoding.geocode(this.indirizzo).subscribe({
      next: (r) => {
        sessionStorage.setItem('marisa_address', r.shortName);
        sessionStorage.setItem('marisa_lat', r.lat.toString());
        sessionStorage.setItem('marisa_lng', r.lng.toString());
        this.indirizzo = r.shortName;
        this.loading = false;
        this.router.navigate(['/restaurant']);
      },
      error: () => {
        this.errore = 'Indirizzo non trovato. Prova a essere più specifico.';
        this.loading = false;
      }
    });
  }

  chiudiSuggerimenti(): void {
    setTimeout(() => { this.mostraSuggerimenti = false; }, 200);
  }

  accedi(): void {
    window.location.href = 'https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev';
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }
}
