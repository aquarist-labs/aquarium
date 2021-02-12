import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CapacityDashboardWidgetComponent } from './capacity-dashboard-widget.component';

describe('CapacityDashboardWidgetComponent', () => {
  let component: CapacityDashboardWidgetComponent;
  let fixture: ComponentFixture<CapacityDashboardWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CapacityDashboardWidgetComponent]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(CapacityDashboardWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
