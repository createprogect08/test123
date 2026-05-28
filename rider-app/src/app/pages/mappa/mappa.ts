import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { RiderService } from '../../services/rider';

@Component({
  selector: 'app-mappa',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './mappa.html',
  styleUrl: './mappa.scss'
})
export class Mappa implements OnInit, OnDestroy {
  idOrdine!: number;
  ordine: any = null;
  fase: 'ristorante' | 'consegna' = 'ristorante';
  loading = true;
  consegnato = false;
  notificaInviata = false;
  stepLoading = false;
  stepErrore = '';
  tokenInserito = '';
  tokenErrore = '';
  tokenConsegnaInserito = '';
  errore = '';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private riderSvc: RiderService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.idOrdine = Number(this.route.snapshot.paramMap.get('idOrdine'));
    this.caricaOrdine();
  }

  caricaOrdine(): void {
    this.riderSvc.getMieiOrdini().subscribe({
      next: res => {
        this.ordine = res.ordini?.find((o: any) => o.id === this.idOrdine);
        if (!this.ordine) this.errore = 'Ordine non trovato';
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.errore = 'Errore caricamento ordine';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  verificaTokenRitiro(): void {
    if (!this.tokenInserito.trim()) return;
    const tokenAtteso = String(this.idOrdine % 1000).padStart(3, '0');
    const tokenInserito = this.tokenInserito.trim().padStart(3, '0');
    if (tokenInserito.toUpperCase() !== tokenAtteso.toUpperCase()) {
      this.tokenErrore = '❌ Codice non valido. Riprova.';
      this.cdr.detectChanges();
      return;
    }
    this.tokenErrore = '';
    this.fase = 'consegna';
    this.cdr.detectChanges();
  }

  segnalaSottoCasa(): void {
    this.stepLoading = true;
    this.cdr.detectChanges();
    this.riderSvc.segnaSottoCasa(this.idOrdine).subscribe({
      next: () => {
        this.notificaInviata = true;
        this.stepLoading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.stepLoading = false;
        this.stepErrore = 'Errore notifica cliente. Riprova.';
        this.cdr.detectChanges();
      }
    });
  }

  segnaConsegnato(): void {
    if (!this.tokenConsegnaInserito.trim()) return;
    this.stepLoading = true;
    this.stepErrore = '';
    this.cdr.detectChanges();
    this.riderSvc.segnaConsegnato(this.idOrdine, this.tokenConsegnaInserito.trim()).subscribe({
      next: () => {
        this.consegnato = true;
        this.stepLoading = false;
        this.cdr.detectChanges();
        setTimeout(() => this.router.navigate(['/']), 2500);
      },
      error: (res: any) => {
        this.stepErrore = res.error?.errore || 'Codice non valido o errore. Riprova.';
        this.stepLoading = false;
        this.cdr.detectChanges();
      }
    });
  }

  ngOnDestroy(): void {}
}
