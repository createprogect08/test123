import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SigninUtente } from './signin-utente';

describe('SigninUtente', () => {
  let component: SigninUtente;
  let fixture: ComponentFixture<SigninUtente>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SigninUtente],
    }).compileComponents();

    fixture = TestBed.createComponent(SigninUtente);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
