/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { HealthDashboardWidgetComponent } from '~/app/core/dashboard/widgets/health-dashboard-widget/health-dashboard-widget.component';
import { Status } from '~/app/shared/services/api/status.service';

describe('HealthDashboardWidgetComponent', () => {
  let component: HealthDashboardWidgetComponent;
  let fixture: ComponentFixture<HealthDashboardWidgetComponent>;
  let mockStatus: Status;
  // @ts-ignore
  const setStatus = (status: string) => (mockStatus.cluster.health.status = status);
  const expectUpdatedFields = ({
    isError = false,
    isWarn = false,
    isOkay = false,
    hasStatus = true,
    statusText,
    boxShadow
  }: {
    isError?: boolean;
    isWarn?: boolean;
    isOkay?: boolean;
    hasStatus?: boolean;
    statusText: string;
    boxShadow: string;
  }) => {
    component.setHealthStatus(mockStatus);
    expect(component.statusText).toBe(statusText);
    expect(component.isError).toBe(isError);
    expect(component.isWarn).toBe(isWarn);
    expect(component.isOkay).toBe(isOkay);
    expect(component.hasStatus).toBe(hasStatus);
    expect(component.setHealthStatusIndicator(mockStatus)).toBe(boxShadow);
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        DashboardModule,
        BrowserAnimationsModule,
        TranslateModule.forRoot(),
        HttpClientTestingModule
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    mockStatus = { cluster: { health: { status: 'health_ok' } } } as Status;
    fixture = TestBed.createComponent(HealthDashboardWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should update fields as expected on health_ok', () => {
    setStatus('health_ok');
    expectUpdatedFields({ statusText: 'OK', boxShadow: 'success', isOkay: true });
  });

  it('should update fields as expected on health_warn', () => {
    setStatus('health_warn');
    expectUpdatedFields({ statusText: 'Warning', boxShadow: 'warning', isWarn: true });
  });

  it('should update fields as expected on health_err', () => {
    setStatus('health_err');
    expectUpdatedFields({ statusText: 'Error', boxShadow: 'error', isError: true });
  });

  it('should update fields as expected while waiting for cluster', () => {
    mockStatus = { cluster: undefined } as Status;
    expectUpdatedFields({ statusText: '', boxShadow: 'info', hasStatus: false });
  });
});
