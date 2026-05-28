import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SigninRistoratore } from './signin-ristoratore';

describe('SigninRistoratore', () => {
  let component: SigninRistoratore;
  let fixture: ComponentFixture<SigninRistoratore>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SigninRistoratore],
    }).compileComponents();

    fixture = TestBed.createComponent(SigninRistoratore);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
