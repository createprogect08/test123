import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Router } from '@angular/router';
import { OrderService } from '../../services/order.service';

@Component({
  standalone: false,
  selector: 'app-wallet',
  templateUrl: './wallet.html',
  styleUrls: ['./wallet.scss']
})
export class WalletComponent implements OnInit {
  saldo = 0;
  transazioni: any[] = [];
  loadingSaldo = true;
  loadingTx = true;
  errore = '';
  modalOpen = false;
  importo = 10;
  ricaricaLoading = false;
  ricaricaErrore = '';
  ricaricaSuccesso = '';

  get loading(): boolean { return this.loadingSaldo || this.loadingTx; }

  constructor(
    private orderService: OrderService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const token = localStorage.getItem('marisa_token');
    if (!token) {
      sessionStorage.setItem('marisa_redirect', '/wallet');
      window.location.href = 'https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev';
      return;
    }
    const params = new URLSearchParams(window.location.search);
    const esito = params.get('ricarica');
    const sessionId = params.get('session_id');
    if (esito === 'ok' && sessionId) {
      this.orderService.verificaRicarica(sessionId).subscribe({
        next: (r) => {
          this.ricaricaSuccesso = `Ricarica completata! Nuovo saldo: €${r.saldo?.toFixed(2)}`;
          this.carica();
        },
        error: (e) => {
          this.ricaricaErrore = e?.error?.errore || 'Errore verifica pagamento.';
          this.carica();
        }
      });
    } else if (esito === 'cancel') {
      this.ricaricaErrore = 'Pagamento annullato.';
      this.carica();
    } else {
      this.carica();
    }
  }

  carica(): void {
    this.loadingSaldo = true;
    this.loadingTx = true;
    this.errore = '';
    this.cdr.detectChanges();

    this.orderService.getSaldo().subscribe({
      next: (r) => {
        this.saldo = r.saldo;
        this.loadingSaldo = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loadingSaldo = false;
        this.errore = 'Errore nel caricamento del saldo.';
        this.cdr.detectChanges();
      }
    });

    this.orderService.getTransazioni().subscribe({
      next: (t) => {
        this.transazioni = t;
        this.loadingTx = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.errore = 'Errore nel caricamento.';
        this.loadingTx = false;
        this.cdr.detectChanges();
      }
    });
  }

  apriModal(): void {
    this.modalOpen = true;
    this.ricaricaErrore = '';
    this.ricaricaSuccesso = '';
    this.importo = 10;
    this.cdr.detectChanges();
  }

  chiudiModal(): void {
    this.modalOpen = false;
    this.ricaricaLoading = false;
    this.cdr.detectChanges();
  }

  confermaRicarica(): void {
    if (this.importo < 1 || this.ricaricaLoading) return;
    this.ricaricaLoading = true;
    this.ricaricaErrore = '';
    this.cdr.detectChanges();

    this.orderService.ricaricaStripe(this.importo).subscribe({
      next: (r) => {
        if (r.stripe_url) {
          window.location.href = r.stripe_url;
        } else {
          this.ricaricaErrore = 'Risposta non valida dal server.';
          this.ricaricaLoading = false;
          this.cdr.detectChanges();
        }
      },
      error: (e) => {
        this.ricaricaErrore = e?.error?.errore || e?.error?.message || 'Errore nella ricarica.';
        this.ricaricaLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  getTipoLabel(tipo: string): string {
    const map: Record<string, string> = {
      ricarica: 'Ricarica',
      pagamento: 'Pagamento ordine',
      rimborso: 'Rimborso'
    };
    return map[tipo] || tipo;
  }

  isEntrata(tipo: string): boolean {
    return tipo === 'ricarica' || tipo === 'rimborso';
  }
}
