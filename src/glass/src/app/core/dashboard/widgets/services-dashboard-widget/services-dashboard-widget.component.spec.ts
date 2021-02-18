import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { ServicesDashboardWidgetComponent } from '~/app/core/dashboard/widgets/services-dashboard-widget/services-dashboard-widget.component';

describe('cephfsDashboardWidgetComponent', () => {
  let component: ServicesDashboardWidgetComponent;
  let fixture: ComponentFixture<ServicesDashboardWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardModule, HttpClientTestingModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ServicesDashboardWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
