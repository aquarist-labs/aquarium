import { ComponentFixture, TestBed } from '@angular/core/testing';

import { BootstrapPageComponent } from './bootstrap-page.component';

describe('BootstrapPageComponent', () => {
  let component: BootstrapPageComponent;
  let fixture: ComponentFixture<BootstrapPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [BootstrapPageComponent]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(BootstrapPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
