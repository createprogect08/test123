import { Component, OnInit } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, CommonModule],
  templateUrl: './header.html',
  styleUrl: './header.scss'
})
export class Header implements OnInit {
  nomeRistorante = '';
  nomeUtente = '';

  constructor(private auth: AuthService) {}

  ngOnInit(): void {
    const user = this.auth.getUser();
    if (user) {
      this.nomeUtente = user.nome || '';
    }
  }

  logout(): void {
    this.auth.logout();
    window.location.href = 'https://reimagined-orbit-r44jxj94649qhpv6-3001.app.github.dev';
  }
}
