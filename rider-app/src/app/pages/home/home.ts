import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { RiderService } from '../../services/rider';
import { WebsocketService } from '../../services/websocket';
import { AuthService } from '../../services/auth';
import { OrdineCard } from '../../components/ordine-card/ordine-card';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, OrdineCard],
  templateUrl: './home.html',
  styleUrl: './home.scss'
})
export class Home implements OnInit, OnDestroy {

  ordini:  any[] = [];
  loading        = true;
  errore         = '';
  utente: any;

  private subs: Subscription[] = [];

  constructor(
    private riderService: RiderService,
    private wsService:    WebsocketService,
    private authService:  AuthService,
    private router:       Router,
    private cdr:          ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.utente = this.authService.getUtente();

    // Se il rider ha già un ordine in_consegna → redirect diretto alla mappa
    this.riderService.getMieiOrdini().subscribe({
      next: res => {
        const inConsegna = res.ordini?.find((o: any) => o.stato === 'in_consegna');
        if (inConsegna) {
          this.router.navigate(['/consegna', inConsegna.id]);
          return;
        }
        this.caricaOrdini();
      },
      error: () => this.caricaOrdini()
    });

    // WebSocket — nuove consegne in real-time
    this.wsService.connect();
    this.subs.push(
      this.wsService.nuovaConsegna$.subscribe(data => {
        const ordine = { ...data.ordine, nuovo: true };
        this.ordini  = [ordine, ...this.ordini.filter(o => o.id !== ordine.id)];
      })
    );
  }

  caricaOrdini(): void {
    this.loading = true;
    this.riderService.getOrdiniDisponibili().subscribe({
      next: res => {
        this.ordini  = res.ordini || [];
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.errore  = 'Errore nel caricamento ordini';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  onAccetta(idOrdine: number): void {
    this.riderService.accettaOrdine(idOrdine).subscribe({
      next: () => this.router.navigate(['/consegna', idOrdine]),
      error: res => {
        const msg = res.error?.errore || '';
        // Se già assegnato a noi → vai comunque alla mappa
        if (msg.includes('in_consegna') || res.status === 409) {
          this.router.navigate(['/consegna', idOrdine]);
        } else {
          this.errore = msg || 'Ordine non più disponibile';
          this.caricaOrdini();
        }
      }
    });
  }

  onRifiuta(idOrdine: number): void {
    this.ordini = this.ordini.filter(o => o.id !== idOrdine);
    this.riderService.rifiutaOrdine(idOrdine).subscribe();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }
}
