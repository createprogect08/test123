import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { map } from 'rxjs/operators';

export interface CartItem {
  id_menu_item: number;
  nome: string;
  prezzo: number;
  quantita: number;
  foto?: string;
}

@Injectable({ providedIn: 'root' })
export class CartService {
  items$ = new BehaviorSubject<CartItem[]>(this.loadFromStorage());
  idRistorante: number | null = this.loadIdRistorante();
  nomeRistorante: string | null = sessionStorage.getItem('marisa_cart_ristorante');

  totale$ = this.items$.pipe(
    map(items => items.reduce((acc, i) => acc + i.prezzo * i.quantita, 0))
  );

  count$ = this.items$.pipe(
    map(items => items.reduce((acc, i) => acc + i.quantita, 0))
  );

  private loadIdRistorante(): number | null {
    const raw = sessionStorage.getItem('marisa_cart_id_ristorante');
    return raw ? parseInt(raw) : null;
  }

  private loadFromStorage(): CartItem[] {
    try {
      const raw = sessionStorage.getItem('marisa_cart');
      return raw ? JSON.parse(raw) : [];
    } catch { return []; }
  }

  private save(items: CartItem[]): void {
    sessionStorage.setItem('marisa_cart', JSON.stringify(items));
  }

  aggiungi(item: CartItem, idRistorante: number, nomeRistorante: string): void {
    if (this.idRistorante && this.idRistorante !== idRistorante) {
      this.clear();
    }
    this.idRistorante = idRistorante;
    this.nomeRistorante = nomeRistorante;
    sessionStorage.setItem('marisa_cart_id_ristorante', String(idRistorante));
    sessionStorage.setItem('marisa_cart_ristorante', nomeRistorante);
    const current = this.items$.getValue();
    const idx = current.findIndex(i => i.id_menu_item === item.id_menu_item);
    if (idx >= 0) {
      current[idx].quantita += 1;
      this.items$.next([...current]);
    } else {
      this.items$.next([...current, { ...item, quantita: 1 }]);
    }
    this.save(this.items$.getValue());
  }

  rimuovi(id_menu_item: number): void {
    const current = this.items$.getValue();
    const idx = current.findIndex(i => i.id_menu_item === id_menu_item);
    if (idx < 0) return;
    if (current[idx].quantita > 1) {
      current[idx].quantita -= 1;
      this.items$.next([...current]);
    } else {
      this.items$.next(current.filter(i => i.id_menu_item !== id_menu_item));
    }
    this.save(this.items$.getValue());
  }

  getQuantita(id_menu_item: number): number {
    return this.items$.getValue().find(i => i.id_menu_item === id_menu_item)?.quantita || 0;
  }

  getCount(): number {
    return this.items$.getValue().reduce((acc, i) => acc + i.quantita, 0);
  }

  clear(): void {
    this.items$.next([]);
    this.idRistorante = null;
    this.nomeRistorante = null;
    sessionStorage.removeItem('marisa_cart');
    sessionStorage.removeItem('marisa_cart_id_ristorante');
    sessionStorage.removeItem('marisa_cart_ristorante');
  }
}
