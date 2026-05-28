import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

@Component({ selector: 'app-do-login', standalone: true, template: '<p style="padding:24px;font-family:Inter,sans-serif;color:#6b7280;">Login in corso...</p>' })
export class DoLogin implements OnInit {
  constructor(private router: Router) {}
  ngOnInit(): void {
    localStorage.setItem('marisa_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwidGlwbyI6InJpZGVyIiwiZXhwIjoxNzc5NDQzODYxLCJpYXQiOjE3NzkzNTc0NjF9.dRqXnxtCrASBvFwUoWLVJv2VA5sYRFWmtlBoP8rNJG4');
    localStorage.setItem('marisa_user', JSON.stringify({id:3, nome:'Luca Rider', tipo:'rider'}));
    this.router.navigate(['/']);
  }
}
