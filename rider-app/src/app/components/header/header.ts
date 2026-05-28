import { Component, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './header.html',
  styleUrl: './header.scss'
})
export class Header implements OnInit {
  nomeUtente = '';

  constructor(private auth: AuthService) {}

  ngOnInit(): void {
    const u = this.auth.getUtente();
    this.nomeUtente = u?.nome || 'Rider';
  }

  logout(): void {
    this.auth.logout();
  }
}
