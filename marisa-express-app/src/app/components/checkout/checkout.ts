import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { Location } from '@angular/common';
import { CartService } from '../../services/cart.service';
import { OrderService } from '../../services/order.service';

@Component({
  standalone: false,
  selector: 'app-checkout',
  templateUrl: './checkout.html',
  styleUrls: ['./checkout.scss']
})
export class CheckoutComponent implements OnInit {
  indirizzo = '';
  saldo = 0;
  metodoPagamento: 'crediti' | 'stripe' = 'crediti';
  loading = false;
  errore = '';

  constructor(
    public cartService: CartService,
    private orderService: OrderService,
    private router: Router,
    private cdr: ChangeDetectorRef,
    private location: Location
  ) {}

  ngOnInit(): void {
    if (this.cartService.getCount() === 0) {
      this.router.navigate(['/']);
      return;
    }
    this.indirizzo = sessionStorage.getItem('marisa_address') || '';
    this.orderService.getSaldo().subscribe({
      next: (r) => (this.saldo = r.saldo),
      error: () => {}
    });
  }


  tornaIndietro(): void {
    this.location.back();
  }

  conferma(): void {
    const items = this.cartService.items$.getValue().map(i => ({
      id_menu_item: i.id_menu_item,
      quantita: i.quantita
    }));
    const lat = parseFloat(sessionStorage.getItem('marisa_lat') || '0');
    const lng = parseFloat(sessionStorage.getItem('marisa_lng') || '0');

    this.loading = true;
    this.errore = '';

    this.orderService.creaOrdine({
      id_ristorante: this.cartService.idRistorante!,
      items,
      indirizzo_consegna: this.indirizzo,
      lat_consegna: lat,
      lng_consegna: lng,
      metodo_pagamento: this.metodoPagamento
    }).subscribe({
      next: (r) => {
        this.cartService.clear();
        if (r.stripe_url) {
          window.location.href = r.stripe_url;
        } else {
          this.router.navigate(['/order', r.id]);
        }
      },
      error: (e) => {
        this.errore = e?.error?.errore || e?.error?.message || "Errore nella creazione dell'ordine.";
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }
}
