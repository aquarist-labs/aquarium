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
/* eslint-disable @typescript-eslint/naming-convention */
import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { EChartsOption } from 'echarts';
import * as _ from 'lodash';
import { forkJoin, Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { bytesToSize, toBytes } from '~/app/functions.helper';
import {
  Device,
  DeviceHost,
  DevicesService,
  DeviceUtilization
} from '~/app/shared/services/api/devices.service';
import { LocalNodeService } from '~/app/shared/services/api/local.service';

type Data = {
  name: string;
  value: number;
  utilization: DeviceUtilization;
  itemStyle: {
    color: string;
  };
};

@Component({
  selector: 'glass-device-utilization-dashboard-widget',
  templateUrl: './device-utilization-dashboard-widget.component.html',
  styleUrls: ['./device-utilization-dashboard-widget.component.scss']
})
export class DeviceUtilizationDashboardWidgetComponent {
  initOpts = {
    height: 'auto',
    width: 'auto'
  };
  options: EChartsOption = {
    // https://colordesigner.io/gradient-generator
    color: [
      '#30ba78',
      '#41b76d',
      '#4eb463',
      '#59b158',
      '#63ae4e',
      '#6daa44',
      '#76a73a',
      '#7ea330',
      '#869f26',
      '#8e9b1d',
      '#959713',
      '#9c9207',
      '#a38d00',
      '#aa8800',
      '#b08300',
      '#b67d00',
      '#bc7700',
      '#c17105',
      '#c76b0f',
      '#cb6417',
      '#cf5d1f',
      '#d35626',
      '#d64e2e',
      '#d94635',
      '#db3e3d',
      '#dc3545'
    ],
    tooltip: {
      position: 'inside',
      formatter: (params) => {
        const total = toBytes(`${_.get(params, 'data.utilization.total_kb')}k`);
        const percent = _.round(_.get(params, 'data.utilization.utilization') * 100, 2);
        return [
          `${_.get(params, 'name')}<br>`,
          `${percent}% ${TEXT('of')} ${bytesToSize(total)}`
        ].join('');
      }
    },
    series: [
      {
        type: 'treemap',
        itemStyle: {
          gapWidth: 1
        },
        label: {
          show: true
        },
        breadcrumb: {
          show: false
        },
        data: []
      }
    ]
  };

  constructor(private devicesService: DevicesService, private localNodeService: LocalNodeService) {}

  updateData(deviceHost: DeviceHost) {
    const data: Array<Data> = [];
    _.forEach(deviceHost.devices, (device: Device) => {
      const value = device.utilization.utilization;
      const index = this.getPaletteIndex(value);
      data.push({
        name: device.path,
        utilization: device.utilization,
        value,
        itemStyle: {
          color: _.get(this.options.color, index)
        }
      });
    });
    _.set(this.options, 'series[0].data', data);
  }

  loadData(): Observable<DeviceHost> {
    return forkJoin({
      inventory: this.localNodeService.inventory(),
      devices: this.devicesService.list()
    }).pipe(map((res) => _.get(res.devices, res.inventory.hostname)));
  }

  getPaletteIndex(percent: number) {
    percent = _.clamp(percent, 0, 1);
    return Math.round(percent * (_.size(this.options.color) - 1));
  }
}
