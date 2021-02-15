/* eslint-disable max-len */
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { CapacityDashboardWidgetComponent } from '~/app/core/dashboard/widgets/capacity-dashboard-widget/capacity-dashboard-widget.component';

describe('CapacityDashboardWidgetComponent', () => {
  let component: CapacityDashboardWidgetComponent;
  let fixture: ComponentFixture<CapacityDashboardWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardModule]
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
