import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-ordine-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ordine-card.html',
  styleUrl: './ordine-card.scss'
})
export class OrdineCard {
  @Input() ordine: any;
  @Output() accetta = new EventEmitter<number>();
  @Output() rifiuta = new EventEmitter<number>();
}
