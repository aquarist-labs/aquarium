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
import { EChartsOption } from 'echarts';
import { Observable } from 'rxjs';

import { translateWords } from '~/app/i18n.helper';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { Inventory, LocalNodeService } from '~/app/shared/services/api/local.service';

@Component({
  selector: 'glass-memory-dashboard-widget',
  templateUrl: './memory-dashboard-widget.component.html',
  styleUrls: ['./memory-dashboard-widget.component.scss']
})
export class MemoryDashboardWidgetComponent {
  ram: {
    inBytes: {
      total: number;
      used: number;
      free: number;
    };
    inPercent: {
      total: number;
      used: number;
      free: number;
    };
    asString: {
      total: string;
      used: string;
      free: string;
    };
  } = {
    inBytes: {
      total: 0,
      used: 0,
      free: 0
    },
    inPercent: {
      total: 100,
      used: 100,
      free: 0
    },
    asString: {
      total: '0 B',
      used: '0 B',
      free: '0 B'
    }
  };
  initOpts = {
    height: 'auto',
    width: 'auto'
  };
  options: EChartsOption = {
    silent: true,
    series: [
      {
        center: ['50%', '50%'],
        itemStyle: {
          color: '#ff9e02'
        },
        progress: {
          show: true,
          width: 20
        },
        pointer: {
          show: false
        },
        axisLine: {
          lineStyle: {
            width: 20
          }
        },
        axisLabel: {
          show: false
        },
        splitLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        type: 'gauge',
        detail: {
          offsetCenter: [0, 0],
          fontSize: 14,
          formatter: '{value}%',
          color: 'auto'
        },
        data: []
      }
    ]
  };
  legend: string[] = [];

  constructor(private localNodeService: LocalNodeService) {}

  updateData(inventory: Inventory) {
    this.updateMemory(inventory);
  }

  loadData(): Observable<Inventory> {
    return this.localNodeService.inventory();
  }

  updateMemory(inventory: Inventory) {
    this.updateRamSpec(inventory);
    const words = translateWords([TEXT('Used'), TEXT('Free'), TEXT('Total')]);
    this.legend = [
      `${words.Total!}: ${this.ram.asString.total}`,
      `${words.Used!}: ${this.ram.asString.used}`,
      `${words.Free!}: ${this.ram.asString.free}`
    ];
    // Somehow TS can't figure out the subtypes of EChartsOption that are already defined.
    // @ts-ignore
    this.options.series[0].data = [{ value: this.ram.inPercent.used }];
  }

  private updateRamSpec(inventory: Inventory) {
    const ramSpec = {
      total: inventory.memory.total_kb,
      free: inventory.memory.free_kb,
      used: inventory.memory.total_kb - inventory.memory.free_kb
    };
    // Note, this implementation is by intention, do NOT use code like
    // 'valueFormatting.bind(this)', otherwise this method is called
    // over and over again because Angular CD seems to assume something
    // has been changed.
    const pipe = new BytesToSizePipe();
    const indexArrTypeSafe: ('total' | 'free' | 'used')[] = ['total', 'free', 'used'];
    indexArrTypeSafe.forEach((s) => {
      this.ram.inBytes[s] = ramSpec[s] * 1024;
      this.ram.inPercent[s] = Math.round((this.ram.inBytes[s] / this.ram.inBytes.total) * 100);
      this.ram.asString[s] = pipe.transform(this.ram.inBytes[s]);
    });
  }
}
