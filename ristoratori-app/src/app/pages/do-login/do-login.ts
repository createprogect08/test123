import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({ selector: 'app-do-login', standalone: true, template: '<p>Login in corso...</p>' })
export class DoLogin implements OnInit {
  constructor(private router: Router) {}
  ngOnInit(): void {
    localStorage.setItem('marisa_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidGlwbyI6InJpc3RvcmF0b3JlIiwiZXhwIjoxNzc5NDQ0OTk4LCJpYXQiOjE3NzkzNTg1OTh9.6HE1b9NZXS_Br-n906428WoOrFjJ8hXuRpLCqmB6btg');
    localStorage.setItem('marisa_user', JSON.stringify({id:6, nome:'Giuseppe Verdi', tipo:'ristoratore'}));
    this.router.navigate(['/']);
  }
}
