/* eslint-disable max-len */
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { CapacityDashboardWidgetComponent } from '~/app/core/dashboard/widgets/capacity-dashboard-widget/capacity-dashboard-widget.component';

describe('CapacityDashboardWidgetComponent', () => {
  let component: CapacityDashboardWidgetComponent;
  let fixture: ComponentFixture<CapacityDashboardWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        DashboardModule,
        HttpClientTestingModule,
        TranslateModule.forRoot(),
        BrowserAnimationsModule
      ]
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
