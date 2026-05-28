import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { OrderService, Ordine } from '../../services/order.service';

@Component({
  standalone: false,
  selector: 'app-storico',
  templateUrl: './storico.html',
  styleUrls: ['./storico.scss']
})
export class StoricoComponent implements OnInit {
  ordini: Ordine[] = [];
  loading = true;
  errore = '';

  constructor(private orderService: OrderService, private router: Router, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    const token = localStorage.getItem('marisa_token');
    if (!token) {
      sessionStorage.setItem('marisa_redirect', '/storico');
      window.location.href = 'https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev';
      return;
    }
    this.orderService.getOrdini().subscribe({
      next: (o) => { this.ordini = o; this.loading = false; this.cdr.detectChanges(); },
      error: (e) => {
        if (e.status === 401) {
          localStorage.removeItem('marisa_token');
          window.location.href = 'https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev';
        } else {
          this.errore = 'Errore nel caricamento degli ordini.';
          this.loading = false;
        }
      }
    });
  }

  getBadgeClass(stato: string): string {
    const map: Record<string, string> = {
      in_attesa: 'badge-attesa', accettato: 'badge-accettato',
      ritirato: 'badge-accettato', sotto_casa: 'badge-consegna',
      in_consegna: 'badge-consegna', consegnato: 'badge-consegnato',
      rifiutato: 'badge-rifiutato', annullato: 'badge-rifiutato'
    };
    return map[stato] || 'badge-attesa';
  }

  getStatoLabel(stato: string): string {
    const map: Record<string, string> = {
      in_attesa: 'In attesa', accettato: 'Rider in arrivo',
      ritirato: 'In consegna', sotto_casa: 'Sotto casa',
      in_consegna: 'In consegna', consegnato: 'Consegnato',
      rifiutato: 'Rifiutato', annullato: 'Annullato'
    };
    return map[stato] || stato;
  }


  apriOrdine(o: any): void {
    const attivi = ['in_attesa', 'accettato', 'ritirato', 'sotto_casa', 'in_consegna'];
    if (attivi.includes(o.stato)) {
      this.router.navigate(['/order', o.id]);
    }
  }

  isAttivo(stato: string): boolean {
    return ['in_attesa', 'accettato', 'ritirato', 'sotto_casa', 'in_consegna'].includes(stato);
  }

  assistenza(id: number): void {
    window.open(`https://reimagined-orbit-r44jxj94649qhpv6-3004.app.github.dev/${id}`, '_blank');
  }
}
