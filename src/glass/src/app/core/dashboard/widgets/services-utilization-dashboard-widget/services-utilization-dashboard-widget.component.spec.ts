/* eslint-disable max-len */
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of } from 'rxjs';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { ServicesUtilizationDashboardWidgetComponent } from '~/app/core/dashboard/widgets/services-utilization-dashboard-widget/services-utilization-dashboard-widget.component';
import { ServicesService, ServiceStorage } from '~/app/shared/services/api/services.service';

describe('ServicesUtilizationDashboardWidgetComponent', () => {
  let component: ServicesUtilizationDashboardWidgetComponent;
  let fixture: ComponentFixture<ServicesUtilizationDashboardWidgetComponent>;
  let servicesService: ServicesService;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        BrowserAnimationsModule,
        DashboardModule,
        HttpClientTestingModule,
        TranslateModule.forRoot()
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(ServicesUtilizationDashboardWidgetComponent);
    component = fixture.componentInstance;
    servicesService = TestBed.inject(ServicesService);
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should convert loaded data', (done) => {
    spyOn(servicesService, 'stats').and.returnValue(
      of({
        foo: {
          name: 'foo',
          utilization: 0.000006287751370776091
        },
        bar: {
          name: 'bar',
          utilization: 0.4227160129839737
        },
        baz: {
          name: 'baz',
          utilization: 0.016
        }
      })
    );
    component.loadData().subscribe((data: Array<Partial<ServiceStorage>>) => {
      expect(data).toEqual([
        {
          name: 'bar',
          utilization: 0.42
        },
        {
          name: 'baz',
          utilization: 0.02
        },
        {
          name: 'foo',
          utilization: 0
        }
      ]);
      done();
    });
  });
});
