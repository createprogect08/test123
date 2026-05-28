import { Component, OnInit, OnDestroy, ChangeDetectorRef, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { RistoranteService } from '../../services/ristorante';
import { WebsocketService } from '../../services/websocket';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.html',
  styleUrl: './home.scss'
})
export class Home implements OnInit, OnDestroy {
  ordiniAttesa: any[] = [];
  ordiniAccettati: any[] = [];
  loading = true;
  errore = '';
  nuovoOrdineId: number | null = null;
  private wsInizializzato = false;
  private subs: Subscription[] = [];

  constructor(
    private ristorante: RistoranteService,
    private ws: WebsocketService,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {}

  ngOnInit(): void {
    this.caricaOrdini();
    this.initWebSocket();
  }

  caricaOrdini(): void {
    this.loading = true;
    this.ristorante.getOrdini('in_attesa').subscribe({
      next: (res) => this.zone.run(() => { this.ordiniAttesa = res.ordini || []; this.loading = false; }),
      error: () => this.zone.run(() => { this.errore = 'Errore caricamento ordini'; this.loading = false; })
    });
    this.ristorante.getOrdini('accettato').subscribe({
      next: (res) => this.zone.run(() => { this.ordiniAccettati = res.ordini || []; }),
      error: () => {}
    });
  }

  initWebSocket(): void {
    if (this.wsInizializzato) return;
    this.wsInizializzato = true;

    this.ristorante.getMe().subscribe({
      next: (res) => {
        const id = res.ristorante?.id;
        if (!id) return;
        this.ws.connect(id);
        this.subs.push(
          this.ws.nuovoOrdine$.subscribe(data => {
            this.zone.run(() => {
              // Ricarica per avere tutti i dati dell'ordine
              this.caricaOrdini();
              this.nuovoOrdineId = data?.ordine?.id;
              setTimeout(() => this.zone.run(() => { this.nuovoOrdineId = null; }), 3000);
            });
          }),
          this.ws.ordineAccettato$.subscribe(() => this.zone.run(() => this.caricaOrdini())),
          this.ws.ordineRifiutato$.subscribe(() => this.zone.run(() => this.caricaOrdini())),
          this.ws.ordineAssegnato$.subscribe(() => this.zone.run(() => this.caricaOrdini())),
          this.ws.ordineAnnullato$.subscribe((data: any) => {
            this.zone.run(() => {
              const id = data?.id_ordine;
              this.ordiniAttesa = this.ordiniAttesa.filter(o => o.id !== id);
              this.ordiniAccettati = this.ordiniAccettati.filter(o => o.id !== id);
            });
          })
        );
      }
    });
  }

  accetta(id: number): void {
    this.ristorante.accettaOrdine(id).subscribe({
      next: () => this.zone.run(() => {
        const o = this.ordiniAttesa.find(x => x.id === id);
        this.ordiniAttesa = this.ordiniAttesa.filter(x => x.id !== id);
        if (o) this.ordiniAccettati = [{ ...o, stato: 'accettato' }, ...this.ordiniAccettati];
      }),
      error: () => alert('Errore accettazione ordine')
    });
  }

  rifiuta(id: number): void {
    const motivo = prompt('Motivo rifiuto (opzionale):') || 'Ordine rifiutato';
    this.ristorante.rifiutaOrdine(id, motivo).subscribe({
      next: () => this.zone.run(() => { this.ordiniAttesa = this.ordiniAttesa.filter(o => o.id !== id); }),
      error: () => alert('Errore rifiuto ordine')
    });
  }

  totale(items: any[]): number {
    if (!items || !items.length) return 0;
    return items.reduce((a, i) => a + (parseFloat(i.prezzo) * (i.quantita || 1)), 0);
  }

  tokenOrdine(id: number): string {
    return String(id % 1000).padStart(3, '0');
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
    this.ws.disconnect();
  }
}
