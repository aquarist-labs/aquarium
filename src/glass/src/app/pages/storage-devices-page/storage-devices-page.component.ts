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
import { Router } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';

import { PageStatus } from '~/app/shared/components/content-page/content-page.component';
import { DatatableActionItem } from '~/app/shared/models/datatable-action-item.type';
import {
  DatatableCellTemplateName,
  DatatableColumn
} from '~/app/shared/models/datatable-column.type';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { DeviceHost, DevicesService, SmartCtl } from '~/app/shared/services/api/devices.service';
import { Disk, Inventory, LocalNodeService } from '~/app/shared/services/api/local.service';

type VolumeExtended = Disk & {
  utilization: number;
  humanReadableUtilization: string;
  // eslint-disable-next-line @typescript-eslint/naming-convention
  smart_metrics?: SmartCtl;
};

@Component({
  selector: 'glass-storage-devices-page',
  templateUrl: './storage-devices-page.component.html',
  styleUrls: ['./storage-devices-page.component.scss']
})
export class StorageDevicesPageComponent {
  @BlockUI()
  blockUI!: NgBlockUI;

  pageStatus: PageStatus = PageStatus.none;
  data: VolumeExtended[] = [];
  columns: DatatableColumn[];

  private firstLoadComplete = false;

  constructor(
    private devicesService: DevicesService,
    private localNodeService: LocalNodeService,
    private router: Router
  ) {
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
        prop: 'rotational',
        cols: 1,
        cellTemplateName: DatatableCellTemplateName.badge,
        cellTemplateConfig: {
          map: {
            true: { value: TEXT('HDD'), class: 'glass-color-theme-gray-600' },
            false: { value: TEXT('NVMe/SSD'), class: 'glass-color-theme-yellow-500' }
          }
        }
      },
      {
        name: TEXT('Size'),
        prop: 'size',
        compareProp: 'size',
        pipe: new BytesToSizePipe()
      },
      {
        name: TEXT('Utilization'),
        prop: 'humanReadableUtilization',
        compareProp: 'utilization'
      },
      {
        name: '',
        prop: '',
        cellTemplateName: DatatableCellTemplateName.actionMenu,
        cellTemplateConfig: this.getActionMenu.bind(this)
      }
    ];
  }

  loadData(): void {
    if (!this.firstLoadComplete) {
      this.pageStatus = PageStatus.loading;
    }
    forkJoin({
      inventory: this.localNodeService.inventory(),
      devices: this.devicesService.list()
    })
      .pipe(
        finalize(() => {
          this.firstLoadComplete = true;
        })
      )
      .subscribe(
        (res: { inventory: Inventory; devices: Record<string, DeviceHost> }) => {
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
                volumeExtended.smart_metrics = device.smart_metrics;
              }
            }
            data.push(volumeExtended);
          });
          this.data = data;
          this.pageStatus = PageStatus.ready;
        },
        () => (this.pageStatus = PageStatus.loadingError)
      );
  }

  private getActionMenu(volume: VolumeExtended): DatatableActionItem[] {
    const encodedPath = encodeURIComponent(volume.path);
    return [
      {
        title: TEXT('Show S.M.A.R.T. data'),
        disabled: !_.isPlainObject(volume.smart_metrics),
        callback: () => this.router.navigate([`dashboard/storage/smart/${encodedPath}`])
      }
    ];
  }
}
