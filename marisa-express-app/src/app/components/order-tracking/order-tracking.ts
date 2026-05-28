import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { Location } from '@angular/common';
import { interval, Subscription } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { OrderService, Ordine } from '../../services/order.service';
import { WebsocketService } from '../../services/websocket.service';

const RIDER_WS = 'https://reimagined-orbit-r44jxj94649qhpv6-5003.app.github.dev';
const RIST_WS  = 'https://reimagined-orbit-r44jxj94649qhpv6-5002.app.github.dev';

const STATI = [
  { key: 'in_attesa',   label: 'Richiesta al ristorante',  icon: '1', desc: 'In attesa che il ristorante accetti' },
  { key: 'accettato',  label: 'Ristorante ha accettato',   icon: '2', desc: 'Il ristorante sta preparando il tuo ordine' },
  { key: 'in_consegna', label: 'Rider ritira ordine',      icon: '3', desc: 'Il rider sta ritirando il tuo ordine al ristorante' },
  { key: 'sotto_casa', label: 'Rider sotto casa',          icon: '4', desc: 'Il rider è arrivato!' },
  { key: 'consegnato', label: 'Ordine completato',         icon: '5', desc: 'Ordine consegnato con successo' },
];

function stimaMinuti(distanzaKm: number | null, statoIndex: number): number {
  const km = distanzaKm ?? 3;
  const totale = km > 5 ? 20 : km > 2 ? 15 : 10;
  const frazioni = [1, 0.8, 0.5, 0.15, 0];
  return Math.round(totale * (frazioni[statoIndex] ?? 0));
}

@Component({
  standalone: false,
  selector: 'app-order-tracking',
  templateUrl: './order-tracking.html',
  styleUrls: ['./order-tracking.scss']
})
export class OrderTrackingComponent implements OnInit, OnDestroy {
  ordine: Ordine | null = null;
  stati = STATI;
  loading = true;
  errore = '';
  annullaLoading = false;
  annullaErrore = '';
  confermaAnnulla = false;
  minutiRimasti = 0;
  tokenInput = '';
  tokenConsegna = '';
  tokenErrore = '';
  tokenLoading = false;
  tokenSuccesso = false;

  private subs: Subscription[] = [];
  private idOrdine = 0;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private orderService: OrderService,
    private ws: WebsocketService,
    private cdr: ChangeDetectorRef,
    public location: Location
  ) {}

  ngOnInit(): void {
    this.idOrdine = Number(this.route.snapshot.paramMap.get('id'));
    this.caricaOrdine();

    const poll = interval(2000).pipe(
      switchMap(() => this.orderService.getOrdine(this.idOrdine))
    ).subscribe(o => { this.ordine = o; if (o.token_consegna) this.tokenConsegna = o.token_consegna; this.aggiornaTimer(); this.cdr.detectChanges(); });
    this.subs.push(poll);

    // WebSocket: fallback visivo immediato, il polling ogni 5s è la fonte di verità
    const consegnato = this.ws.on<{ id_ordine: number }>(RIDER_WS, 'ordine_consegnato')
      .subscribe(() => { if (this.ordine) { this.ordine.stato = 'consegnato'; this.aggiornaTimer(); this.cdr.detectChanges(); } });
    this.subs.push(consegnato);

    const assegnato = this.ws.on<{ id_ordine: number }>(RIDER_WS, 'ordine_assegnato')
      .subscribe(() => { if (this.ordine) { this.ordine.stato = 'in_consegna'; this.aggiornaTimer(); this.cdr.detectChanges(); } });
    this.subs.push(assegnato);

    const sottoCasa = this.ws.on<{ id_ordine: number, token: string }>(RIDER_WS, 'rider_sotto_casa')
      .subscribe((data) => { if (this.ordine) { this.ordine.stato = 'sotto_casa'; this.tokenConsegna = data?.token || this.ordine.token_consegna || ''; this.aggiornaTimer(); this.cdr.detectChanges(); } });
    this.subs.push(sottoCasa);
  }

  caricaOrdine(): void {
    this.orderService.getOrdine(this.idOrdine).subscribe({
      next: (o) => {
        this.ordine = o;
        if (o.stato === 'sotto_casa' && o.token_consegna) this.tokenConsegna = o.token_consegna;
        this.loading = false;
        this.aggiornaTimer();
        this.cdr.detectChanges();
      },
      error: () => {
        this.errore = 'Ordine non trovato.';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  aggiornaTimer(): void {
    if (!this.ordine) return;
    const idx = this.getStatoIndex();
    this.minutiRimasti = stimaMinuti((this.ordine as any).distanza_km ?? null, idx);
  }

  getStatoIndex(): number {
    if (!this.ordine) return 0;
    const idx = this.stati.findIndex(s => s.key === this.ordine!.stato);
    return idx >= 0 ? idx : 0;
  }

  getProgressPercent(): number {
    return Math.round((this.getStatoIndex() / (this.stati.length - 1)) * 100);
  }

  isCompleted(i: number): boolean { return i < this.getStatoIndex(); }
  isActive(i: number): boolean    { return i === this.getStatoIndex(); }

  puoAnnullare(): boolean {
    return !!this.ordine && (this.ordine.stato === 'in_attesa' || this.ordine.stato === 'accettato');
  }

  ordineSottoCasa(): boolean {
    return !!this.ordine && this.ordine.stato === 'sotto_casa';
  }

  confermaToken(): void {
    if (!this.tokenInput.trim()) return;
    this.tokenLoading = true;
    this.tokenErrore = '';
    this.cdr.detectChanges();
    this.orderService.confermaTokenConsegna(this.idOrdine, this.tokenInput.trim()).subscribe({
      next: () => {
        this.tokenSuccesso = true;
        this.tokenLoading = false;
        if (this.ordine) this.ordine.stato = 'consegnato';
        this.cdr.detectChanges();
      },
      error: (e: any) => {
        this.tokenErrore = e?.error?.errore || 'Token non valido.';
        this.tokenLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  annulla(): void {
    if (!this.confermaAnnulla) { this.confermaAnnulla = true; this.cdr.detectChanges(); return; }
    this.annullaLoading = true;
    this.annullaErrore = '';
    this.cdr.detectChanges();
    this.orderService.annullaOrdine(this.idOrdine).subscribe({
      next: () => {
        this.annullaLoading = false;
        if (this.ordine) this.ordine.stato = 'annullato';
        this.cdr.detectChanges();
        setTimeout(() => this.router.navigate(['/storico']), 1500);
      },
      error: (e: any) => {
        this.annullaErrore = e?.error?.errore || "Errore durante l'annullamento.";
        this.annullaLoading = false;
        this.confermaAnnulla = false;
        this.cdr.detectChanges();
      }
    });
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
    this.ws.disconnect(RIDER_WS);
    this.ws.disconnect(RIST_WS);
  }
}
