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
import { LoadDashboardWidgetComponent } from '~/app/core/dashboard/widgets/load-dashboard-widget/load-dashboard-widget.component';
import { WidgetHealthStatus } from '~/app/shared/components/widget/widget.component';
import { TestingModule } from '~/app/testing.module';

describe('LoadDashboardWidgetComponent', () => {
  let component: LoadDashboardWidgetComponent;
  let fixture: ComponentFixture<LoadDashboardWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DashboardModule, TestingModule, TranslateModule.forRoot()]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(LoadDashboardWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should return status [1]', () => {
    expect(component.getStatusClass(1)).toBe(WidgetHealthStatus.info);
    expect(component.getStatusClass(50)).toBe(WidgetHealthStatus.info);
  });

  it('should return status [2]', () => {
    expect(component.getStatusClass(51)).toBe(WidgetHealthStatus.warning);
    expect(component.getStatusClass(100)).toBe(WidgetHealthStatus.warning);
  });

  it('should return status [3]', () => {
    expect(component.getStatusClass(101)).toBe(WidgetHealthStatus.error);
    expect(component.getStatusClass(144)).toBe(WidgetHealthStatus.error);
  });

  it('should return status [4]', () => {
    expect(
      component.setStatus([
        { name: 'foo', percent: 44 },
        { name: 'bar', percent: 30 },
        { name: 'baz', percent: 10 }
      ])
    ).toBe(WidgetHealthStatus.info);
    expect(
      component.setStatus([
        { name: 'foo', percent: 44 },
        { name: 'bar', percent: 65 },
        { name: 'baz', percent: 90 }
      ])
    ).toBe(WidgetHealthStatus.warning);
    expect(
      component.setStatus([
        { name: 'foo', percent: 44 },
        { name: 'bar', percent: 65 },
        { name: 'baz', percent: 105 }
      ])
    ).toBe(WidgetHealthStatus.error);
  });
});
