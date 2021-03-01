import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { HostsDashboardWidgetComponent } from '~/app/core/dashboard/widgets/hosts-dashboard-widget/hosts-dashboard-widget.component';

describe('HostsDashboardWidgetComponent', () => {
  let component: HostsDashboardWidgetComponent;
  let fixture: ComponentFixture<HostsDashboardWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardModule, HttpClientTestingModule]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(HostsDashboardWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
