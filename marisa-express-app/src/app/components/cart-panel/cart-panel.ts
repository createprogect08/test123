import { Component, Output, EventEmitter } from '@angular/core';
import { CartService, CartItem } from '../../services/cart.service';

@Component({
  standalone: false,
  selector: 'app-cart-panel',
  templateUrl: './cart-panel.html',
  styleUrls: ['./cart-panel.scss']
})
export class CartPanelComponent {
  @Output() checkout = new EventEmitter<void>();

  constructor(public cartService: CartService) {}

  aggiungi(item: CartItem): void {
    if (!this.cartService.idRistorante || !this.cartService.nomeRistorante) return;
    this.cartService.aggiungi(
      { ...item, quantita: 1 },
      this.cartService.idRistorante,
      this.cartService.nomeRistorante
    );
  }

  rimuovi(id: number): void {
    this.cartService.rimuovi(id);
  }

  svuota(): void {
    this.cartService.clear();
  }
}
