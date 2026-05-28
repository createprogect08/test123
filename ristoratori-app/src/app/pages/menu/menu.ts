import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RistoranteService } from '../../services/ristorante';

const BACKEND = '/main';

@Component({
  selector: 'app-menu',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './menu.html',
  styleUrl: './menu.scss'
})
export class Menu implements OnInit {
  items: any[] = [];
  categorie: string[] = [];
  loading = true;
  errore = '';
  salvataggio = false;

  showForm = false;
  editingId: number | null = null;

  form = { nome: '', descrizione: '', prezzo: 0, categoria: '', disponibile: true };
  immagineFile: File | null = null;
  immaginePreview: string | null = null;

  constructor(private ristorante: RistoranteService) {}

  ngOnInit(): void { this.caricaMenu(); }

  caricaMenu(): void {
    this.loading = true;
    this.ristorante.getMenu().subscribe({
      next: (res) => {
        this.items = res.menu || [];
        this.categorie = res.categorie || [];
        this.loading = false;
      },
      error: () => { this.errore = 'Errore caricamento menu'; this.loading = false; }
    });
  }

  fotoUrl(foto: string | null): string | null {
    if (!foto) return null;
    if (foto.startsWith('http')) return foto;
    return BACKEND + foto;
  }

  apriForm(item?: any): void {
    if (item) {
      this.editingId = item.id;
      this.form = {
        nome: item.nome,
        descrizione: item.descrizione || '',
        prezzo: item.prezzo,
        categoria: item.categoria || '',
        disponibile: item.disponibile
      };
      this.immaginePreview = this.fotoUrl(item.foto);
    } else {
      this.editingId = null;
      this.form = { nome: '', descrizione: '', prezzo: 0, categoria: '', disponibile: true };
      this.immaginePreview = null;
    }
    this.immagineFile = null;
    this.showForm = true;
  }

  chiudiForm(): void {
    this.showForm = false;
    this.editingId = null;
    this.immagineFile = null;
    this.immaginePreview = null;
  }

  onImmagineSelezionata(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      this.immagineFile = input.files[0];
      const reader = new FileReader();
      reader.onload = (e) => { this.immaginePreview = e.target?.result as string; };
      reader.readAsDataURL(this.immagineFile);
    }
  }

  salva(): void {
    if (!this.form.nome || !this.form.prezzo) return;
    this.salvataggio = true;

    let op;
    if (this.immagineFile) {
      const fd = new FormData();
      fd.append('nome', this.form.nome);
      fd.append('descrizione', this.form.descrizione);
      fd.append('prezzo', String(this.form.prezzo));
      fd.append('categoria', this.form.categoria);
      fd.append('disponibile', String(this.form.disponibile));
      fd.append('immagine', this.immagineFile);

      op = this.editingId
        ? this.ristorante.modificaItemFormData(this.editingId, fd)
        : this.ristorante.creaItemFormData(fd);
    } else {
      op = this.editingId
        ? this.ristorante.modificaItem(this.editingId, this.form)
        : this.ristorante.creaItem(this.form);
    }

    op.subscribe({
      next: () => { this.caricaMenu(); this.chiudiForm(); this.salvataggio = false; },
      error: () => { alert('Errore salvataggio'); this.salvataggio = false; }
    });
  }

  elimina(id: number, nome: string): void {
    if (!confirm(`Eliminare "${nome}"?`)) return;
    this.ristorante.eliminaItem(id).subscribe({
      next: () => { this.items = this.items.filter(i => i.id !== id); },
      error: () => alert('Errore eliminazione')
    });
  }

  toggleDisponibile(item: any): void {
    this.ristorante.modificaItem(item.id, { disponibile: !item.disponibile }).subscribe({
      next: () => { item.disponibile = !item.disponibile; }
    });
  }
}
