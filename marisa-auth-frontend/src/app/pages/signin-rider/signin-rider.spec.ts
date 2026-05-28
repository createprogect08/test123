import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SigninRider } from './signin-rider';

describe('SigninRider', () => {
  let component: SigninRider;
  let fixture: ComponentFixture<SigninRider>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SigninRider],
    }).compileComponents();

    fixture = TestBed.createComponent(SigninRider);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
