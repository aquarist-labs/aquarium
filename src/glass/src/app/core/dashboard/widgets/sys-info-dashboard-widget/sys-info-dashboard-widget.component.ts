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
import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { translate } from '~/app/i18n.helper';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { Inventory, LocalNodeService } from '~/app/shared/services/api/local.service';

@Component({
  selector: 'glass-sys-info-dashboard-widget',
  templateUrl: './sys-info-dashboard-widget.component.html',
  styleUrls: ['./sys-info-dashboard-widget.component.scss']
})
export class SysInfoDashboardWidgetComponent {
  data: Inventory = {} as Inventory;
  memoryChartData: any[] = [];
  memoryChartColorScheme = {
    // EOS colors: [$eos-bc-green-500, $eos-bc-gray-100]
    domain: ['#30ba78', '#e0dfdf']
  };
  cpuLoadChartData: any[] = [];
  cpuLoadColorScheme = {
    // EOS colors: [$eos-bc-yellow-100, $eos-bc-yellow-500, $eos-bc-yellow-900]
    domain: ['#ffecb5', '#ffc107', '#ff9e02']
  };

  constructor(
    private bytesToSizePipe: BytesToSizePipe,
    private localNodeService: LocalNodeService
  ) {}

  valueFormatting(c: any) {
    return this.bytesToSizePipe.transform(c);
  }

  updateData($data: Inventory) {
    this.data = $data;
  }

  loadData(): Observable<Inventory> {
    return this.localNodeService.inventory().pipe(
      map((inventory: Inventory) => {
        const total: number = inventory.memory.total_kb * 1024;
        const free: number = inventory.memory.free_kb * 1024;
        this.memoryChartData = [
          {
            name: translate(TEXT('Used')),
            value: total - free
          },
          {
            name: translate(TEXT('Free')),
            value: free
          }
        ];
        /* eslint-disable @typescript-eslint/naming-convention */
        const load_1min = Math.floor(inventory.cpu.load.one_min * 100);
        const load_5min = Math.floor(inventory.cpu.load.five_min * 100);
        const load_15min = Math.floor(inventory.cpu.load.fifteen_min * 100);
        this.cpuLoadChartData = [
          { name: translate(TEXT('1min')), value: `${load_1min}%` },
          { name: translate(TEXT('5min')), value: `${load_5min}%` },
          { name: translate(TEXT('15min')), value: `${load_15min}%` }
        ];
        // Modify the uptime value to allow the `relativeDate` pipe
        // to calculate the correct time to display.
        inventory.system_uptime = inventory.system_uptime * -1;
        return inventory;
      })
    );
  }
}
