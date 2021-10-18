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
/* eslint-disable max-len */
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TranslateModule } from '@ngx-translate/core';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { DeviceUtilizationDashboardWidgetComponent } from '~/app/core/dashboard/widgets/device-utilization-dashboard-widget/device-utilization-dashboard-widget.component';
import { TestingModule } from '~/app/testing.module';

describe('DeviceUtilizationDashboardWidgetComponent', () => {
  let component: DeviceUtilizationDashboardWidgetComponent;
  let fixture: ComponentFixture<DeviceUtilizationDashboardWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardModule, TestingModule, TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(DeviceUtilizationDashboardWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should get palette index', () => {
    expect(component.getPaletteIndex(0.99)).toBe(25);
    expect(component.getPaletteIndex(0.9)).toBe(23);
    expect(component.getPaletteIndex(0.1)).toBe(3);
    expect(component.getPaletteIndex(0.01)).toBe(0);
    expect(component.getPaletteIndex(1.2)).toBe(25);
    expect(component.getPaletteIndex(-0.2)).toBe(0);
  });
});
