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
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TranslateModule } from '@ngx-translate/core';

import { DashboardModule } from '~/app/core/dashboard/dashboard.module';
import { SysInfoDashboardWidgetComponent } from '~/app/core/dashboard/widgets/sys-info-dashboard-widget/sys-info-dashboard-widget.component';
import { Inventory } from '~/app/shared/services/api/local.service';

describe('SysInfoDashboardWidgetComponent', () => {
  let component: SysInfoDashboardWidgetComponent;
  let fixture: ComponentFixture<SysInfoDashboardWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        DashboardModule,
        TranslateModule.forRoot(),
        HttpClientTestingModule,
        BrowserAnimationsModule
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SysInfoDashboardWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  describe('Memory', () => {
    let inventoryMock: Inventory;
    beforeEach(() => {
      inventoryMock = {
        memory: {
          // eslint-disable-next-line @typescript-eslint/naming-convention
          total_kb: 100,
          // eslint-disable-next-line @typescript-eslint/naming-convention
          free_kb: 95
        }
      } as Inventory;
      component.updateMemory(inventoryMock);
    });

    it('should calculate memory usage in percent', () => {
      expect(component.ram).toEqual({
        inBytes: {
          total: 102400,
          used: 5120,
          free: 97280
        },
        inPercent: {
          total: 100,
          used: 5,
          free: 95
        },
        asString: {
          total: '100 KB',
          used: '5 KB',
          free: '95 KB'
        }
      });
    });

    it('should show the right gauge text', () => {
      // @ts-ignore
      expect(component.memoryGaugeOpts.title.subtext).toBe(
        'Total: 100 KB\nUsed: 5 KB\nFree: 95 KB'
      );
    });
  });
});
