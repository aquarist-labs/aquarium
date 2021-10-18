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
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { bytesToSize, toBytes } from '~/app/functions.helper';
import {
  Device,
  DeviceHost,
  DevicesService,
  DeviceUtilization
} from '~/app/shared/services/api/devices.service';

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
      '#00b2e2',
      '#0aafe6',
      '#1bace9',
      '#2ba8eb',
      '#3aa4ed',
      '#49a0ee',
      '#589cee',
      '#6697ed',
      '#7492eb',
      '#818ce8',
      '#8d87e4',
      '#9981df',
      '#a57ad9',
      '#af74d2',
      '#b96dca',
      '#c266c1',
      '#ca5fb7',
      '#d157ac',
      '#d650a1',
      '#db4995',
      '#de4388',
      '#e03d7b',
      '#e1396e',
      '#e13660',
      '#df3453',
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

  constructor(private devicesService: DevicesService) {}

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
    return this.devicesService.list().pipe(map((data) => _.get(_.values(data), 0)));
  }

  getPaletteIndex(percent: number) {
    percent = _.clamp(percent, 0, 1);
    return Math.round(percent * (_.size(this.options.color) - 1));
  }
}
