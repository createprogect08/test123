import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RiderService } from '../../services/rider';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-setting',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './setting.html',
  styleUrl: './setting.scss'
})
export class Setting implements OnInit {

  utente: any  = null;
  rider:  any  = null;
  loading      = true;
  salvando     = false;
  successo     = '';
  errore       = '';

  form = {
    veicolo:    '',
    targa:      '',
    disponibile: true
  };

  fotoFile: File | null = null;
  fotoPreview: string   = '';

  constructor(
    private riderSvc: RiderService,
    private authSvc:  AuthService,
    private cdr:      ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.riderSvc.getMe().subscribe({
      next: res => {
        this.utente = res.utente;
        this.rider  = res.rider;
        this.form.veicolo     = res.rider.veicolo     || '';
        this.form.targa       = res.rider.targa        || '';
        this.form.disponibile = res.rider.disponibile  === 1;
        this.fotoPreview      = res.rider.foto_profilo
          ? `/rider${res.rider.foto_profilo}`
          : '';
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.errore  = 'Errore caricamento profilo';
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  onFotoChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file  = input.files?.[0];
    if (!file) return;
    this.fotoFile = file;
    const reader  = new FileReader();
    reader.onload = e => this.fotoPreview = e.target?.result as string;
    reader.readAsDataURL(file);
  }

  salva(): void {
    this.salvando = true;
    this.successo = '';
    this.errore   = '';

    const fd = new FormData();
    fd.append('veicolo',     this.form.veicolo);
    fd.append('targa',       this.form.targa);
    fd.append('disponibile', this.form.disponibile ? '1' : '0');
    if (this.fotoFile) fd.append('foto', this.fotoFile);

    this.riderSvc.updateMe(fd).subscribe({
      next: () => {
        this.successo = 'Profilo aggiornato con successo!';
        this.salvando = false;
      },
      error: res => {
        this.errore   = res.error?.errore || 'Errore salvataggio';
        this.salvando = false;
      }
    });
  }

  logout(): void {
    this.authSvc.logout();
  }
}
