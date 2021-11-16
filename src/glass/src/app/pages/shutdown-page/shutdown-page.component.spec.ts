import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ShutdownPageComponent } from '~/app/pages/shutdown-page/shutdown-page.component';

describe('ShutdownPageComponent', () => {
  let component: ShutdownPageComponent;
  let fixture: ComponentFixture<ShutdownPageComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ShutdownPageComponent]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ShutdownPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
