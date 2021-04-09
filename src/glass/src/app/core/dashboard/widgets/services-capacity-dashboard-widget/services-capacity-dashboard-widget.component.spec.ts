/* eslint-disable max-len */
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';
import { of } from 'rxjs';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { ServicesCapacityDashboardWidgetComponent } from '~/app/core/dashboard/widgets/services-capacity-dashboard-widget/services-capacity-dashboard-widget.component';
import { ServicesService, ServiceStorage } from '~/app/shared/services/api/services.service';

describe('ServicesCapacityDashboardWidgetComponent', () => {
  let component: ServicesCapacityDashboardWidgetComponent;
  let fixture: ComponentFixture<ServicesCapacityDashboardWidgetComponent>;
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
    fixture = TestBed.createComponent(ServicesCapacityDashboardWidgetComponent);
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
          utilization: 0.00004227160129839737
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
          name: 'foo',
          utilization: 0
        },
        {
          name: 'bar',
          utilization: 0
        },
        {
          name: 'baz',
          utilization: 0.02
        }
      ]);
      done();
    });
  });
});
