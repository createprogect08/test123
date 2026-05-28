import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RistoranteService } from '../../services/ristorante';

@Component({
  selector: 'app-setting',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './setting.html',
  styleUrl: './setting.scss'
})
export class Setting implements OnInit {
  loading = true;
  salvataggio = false;
  successo = false;
  errore = '';

  form: any = {
    nome: '', descrizione: '', via: '',
    telefono: '', partita_iva: '', categoria: ''
  };

  fotoPreview: string | null = null;
  fotoFile: File | null = null;

  constructor(private ristorante: RistoranteService) {}

  ngOnInit(): void {
    this.ristorante.getMe().subscribe({
      next: (res) => {
        const r = res.ristorante || {};
        this.form = {
          nome: r.nome || '', descrizione: r.descrizione || '',
          via: r.via || '', telefono: r.telefono || '',
          partita_iva: r.partita_iva || '', categoria: r.categoria || ''
        };
        if (r.foto_profilo) this.fotoPreview = `/main${r.foto_profilo}`;
        this.loading = false;
      },
      error: () => { this.errore = 'Errore caricamento dati'; this.loading = false; }
    });
  }

  onFoto(event: any): void {
    const file = event.target.files?.[0];
    if (!file) return;
    this.fotoFile = file;
    const reader = new FileReader();
    reader.onload = (e: any) => { this.fotoPreview = e.target.result; };
    reader.readAsDataURL(file);
  }

  salva(): void {
    this.salvataggio = true;
    this.successo = false;
    this.errore = '';

    const fd = new FormData();
    Object.keys(this.form).forEach(k => fd.append(k, this.form[k]));
    if (this.fotoFile) fd.append('foto', this.fotoFile);

    this.ristorante.updateMe(fd).subscribe({
      next: () => {
        this.salvataggio = false;
        this.successo = true;
        setTimeout(() => this.successo = false, 3000);
      },
      error: () => {
        this.salvataggio = false;
        this.errore = 'Errore salvataggio dati';
      }
    });
  }
}
