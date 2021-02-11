import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { DevicesDashboardWidgetComponent } from '~/app/core/dashboard/widgets/devices-dashboard-widget/devices-dashboard-widget.component';

describe('DevicesDashboardWidgetComponent', () => {
  let component: DevicesDashboardWidgetComponent;
  let fixture: ComponentFixture<DevicesDashboardWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DevicesDashboardWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
