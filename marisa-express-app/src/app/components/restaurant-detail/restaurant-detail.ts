import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Location } from '@angular/common';
import { RestaurantService, Ristorante, MenuItem } from '../../services/restaurant.service';
import { CartService } from '../../services/cart.service';

@Component({
  standalone: false,
  selector: 'app-restaurant-detail',
  templateUrl: './restaurant-detail.html',
  styleUrls: ['./restaurant-detail.scss']
})
export class RestaurantDetailComponent implements OnInit {
  ristorante: Ristorante | null = null;
  menu: MenuItem[] = [];
  loading = true;
  errore = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    public location: Location,
    private restaurantService: RestaurantService,
    public cartService: CartService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.restaurantService.getRistorante(id).subscribe({
      next: (r) => { this.ristorante = r; this.loading = false; this.cdr.detectChanges(); },
      error: () => { this.errore = 'Ristorante non trovato.'; this.loading = false; this.cdr.detectChanges(); }
    });
    this.restaurantService.getMenu(id).subscribe({
      next: (m) => { this.menu = m; this.cdr.detectChanges(); },
      error: () => {}
    });
  }

  getQuantita(id: number): number { return this.cartService.getQuantita(id); }

  aggiungi(item: MenuItem): void {
    if (!this.ristorante) return;
    this.cartService.aggiungi({
      id_menu_item: item.id,
      nome: item.nome,
      prezzo: item.prezzo,
      quantita: 1,
      foto: item.foto
    }, this.ristorante.id, this.ristorante.nome);
  }

  rimuovi(item: MenuItem): void { this.cartService.rimuovi(item.id); }

  vaiCheckout(): void {
    const token = localStorage.getItem('marisa_token');
    if (token) {
      this.router.navigate(['/checkout']);
    } else {
      sessionStorage.setItem('marisa_redirect', '/checkout');
      window.location.href = 'https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev';
    }
  }

  getFoto(url: string | undefined): string {
    return url || '';
  }
}
