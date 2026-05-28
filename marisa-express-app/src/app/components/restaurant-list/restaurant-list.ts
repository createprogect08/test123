import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import { RestaurantService, Ristorante } from '../../services/restaurant.service';
import { GeocodingService, GeoResult } from '../../services/geocoding.service';

const CATEGORIE = [
  { label: 'Tutti', value: '' },
  { label: '🍔 Burger', value: 'burger' },
  { label: '🍕 Pizza', value: 'pizza' },
  { label: '🥙 Piadina', value: 'piadina' },
  { label: '🍣 Sushi', value: 'sushi' },
  { label: '🥗 Insalate', value: 'insalate' },
  { label: '🍝 Pasta', value: 'pasta' },
  { label: '🌮 Messicano', value: 'messicano' },
];

@Component({
  standalone: false,
  selector: 'app-restaurant-list',
  templateUrl: './restaurant-list.html',
  styleUrls: ['./restaurant-list.scss']
})
export class RestaurantListComponent implements OnInit {
  ristoranti: Ristorante[] = [];
  filtrati: Ristorante[] = [];
  categorie = CATEGORIE;
  categoriaAttiva = '';
  indirizzo = '';
  loading = true;
  errore = '';
  cercaIndirizzo = '';
  cercaLoading = false;
  cercaErrore = '';
  mostraFormIndirizzo = false;
  suggerimenti: GeoResult[] = [];

  private search$ = new Subject<string>();

  constructor(
    private restaurantService: RestaurantService,
    private geocoding: GeocodingService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const lat = sessionStorage.getItem('marisa_lat');
    const lng = sessionStorage.getItem('marisa_lng');
    this.indirizzo = sessionStorage.getItem('marisa_address') || '';

    if (!lat || !lng) {
      this.mostraFormIndirizzo = true;
      this.loading = false;
    } else {
      this.caricaRistoranti(parseFloat(lat), parseFloat(lng));
    }

    this.search$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(q => q.length >= 3 ? this.geocoding.suggest(q) : [])
    ).subscribe(res => {
      this.suggerimenti = res;
      this.cdr.detectChanges();
    });
  }

  onInput(): void {
    this.suggerimenti = [];
    this.search$.next(this.cercaIndirizzo);
  }

  selezionaSuggerimento(r: GeoResult): void {
    this.suggerimenti = [];
    this.cercaIndirizzo = r.shortName;
    this.applicaGeoResult(r);
  }

  impostaIndirizzo(): void {
    if (!this.cercaIndirizzo.trim()) return;
    this.suggerimenti = [];
    this.cercaLoading = true;
    this.cercaErrore = '';
    this.cdr.detectChanges();
    this.geocoding.geocode(this.cercaIndirizzo).subscribe({
      next: r => this.applicaGeoResult(r),
      error: () => {
        this.cercaErrore = 'Indirizzo non trovato.';
        this.cercaLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  private applicaGeoResult(r: GeoResult): void {
    sessionStorage.setItem('marisa_address', r.shortName);
    sessionStorage.setItem('marisa_lat', r.lat.toString());
    sessionStorage.setItem('marisa_lng', r.lng.toString());
    this.indirizzo = r.shortName;
    this.mostraFormIndirizzo = false;
    this.cercaLoading = false;
    this.caricaRistoranti(r.lat, r.lng);
  }

  caricaRistoranti(lat: number, lng: number): void {
    this.loading = true;
    this.errore = '';
    this.cdr.detectChanges();
    this.restaurantService.getVicini(lat, lng).subscribe({
      next: data => {
        this.ristoranti = data;
        this.appliFiltro();
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.errore = 'Errore nel caricamento dei ristoranti.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  selezionaCategoria(cat: string): void {
    this.categoriaAttiva = cat;
    this.appliFiltro();
  }

  appliFiltro(): void {
    this.filtrati = this.categoriaAttiva
      ? this.ristoranti.filter(r => (r.categoria || '').toLowerCase() === this.categoriaAttiva.toLowerCase())
      : [...this.ristoranti];
  }

  apriRistorante(id: number): void {
    this.router.navigate(['/restaurant', id]);
  }

  modificaIndirizzo(): void {
    this.mostraFormIndirizzo = true;
    this.cercaIndirizzo = '';
    this.suggerimenti = [];
    this.cercaErrore = '';
  }
}
