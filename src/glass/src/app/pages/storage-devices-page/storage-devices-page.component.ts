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
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';

import {
  DatatableCellTemplateName,
  DatatableColumn
} from '~/app/shared/models/datatable-column.type';
import { DeviceHost, DevicesService } from '~/app/shared/services/api/devices.service';
import { Disk, Inventory, LocalNodeService } from '~/app/shared/services/api/local.service';

type VolumeExtended = Disk & {
  utilization: number;
  humanReadableUtilization: string;
};

@Component({
  selector: 'glass-storage-devices-page',
  templateUrl: './storage-devices-page.component.html',
  styleUrls: ['./storage-devices-page.component.scss']
})
export class StorageDevicesPageComponent {
  @BlockUI()
  blockUI!: NgBlockUI;

  loading = false;
  firstLoadComplete = false;
  data: VolumeExtended[] = [];
  columns: DatatableColumn[];

  constructor(private devicesService: DevicesService, private localNodeService: LocalNodeService) {
    this.columns = [
      {
        name: TEXT('Path'),
        prop: 'path'
      },
      {
        name: TEXT('Serial'),
        prop: 'id'
      },
      {
        name: TEXT('Vendor'),
        prop: 'vendor'
      },
      {
        name: TEXT('Type'),
        prop: 'human_readable_type',
        cellTemplateName: DatatableCellTemplateName.badge,
        cellTemplateConfig: {
          map: {
            hdd: { value: TEXT('HDD'), class: 'glass-color-theme-gray-600' },
            ssd: { value: TEXT('SSD'), class: 'glass-color-theme-cerulean-500' },
            'nvme/ssd': { value: TEXT('NVMe/SSD'), class: 'glass-color-theme-yellow-500' }
          }
        }
      },
      {
        name: TEXT('Size'),
        prop: 'size',
        compareProp: 'size'
      },
      {
        name: TEXT('Utilization'),
        prop: 'humanReadableUtilization',
        compareProp: 'utilization'
      }
    ];
  }

  loadData(): void {
    this.loading = true;
    forkJoin({
      inventory: this.localNodeService.inventory(),
      devices: this.devicesService.list()
    })
      .pipe(
        finalize(() => {
          this.loading = this.firstLoadComplete = true;
        })
      )
      .subscribe((res: { inventory: Inventory; devices: Record<string, DeviceHost> }) => {
        const data: VolumeExtended[] = [];
        _.forEach(res.inventory.disks, (disk: Disk) => {
          const volumeExtended: VolumeExtended = disk as VolumeExtended;
          // Append the utilization.
          const deviceHost: DeviceHost = _.get(res.devices, res.inventory.hostname);
          if (deviceHost) {
            const device = _.find(deviceHost.devices, ['path', disk.path]);
            if (device) {
              volumeExtended.utilization = device.utilization.utilization;
              volumeExtended.humanReadableUtilization = `${_.round(
                device.utilization.utilization * 100,
                2
              )}%`;
            }
          }
          data.push(volumeExtended);
        });
        this.data = data;
      });
  }
}
