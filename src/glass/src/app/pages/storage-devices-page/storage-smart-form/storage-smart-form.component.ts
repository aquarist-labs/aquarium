import { Component } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { forkJoin } from 'rxjs';
import { finalize } from 'rxjs/operators';

import { PageStatus } from '~/app/shared/components/content-page/content-page.component';
import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import {
  Device,
  DeviceHost,
  DevicesService,
  SmartCtlAtaSmartAttribute
} from '~/app/shared/services/api/devices.service';
import { Inventory, LocalNodeService } from '~/app/shared/services/api/local.service';

@Component({
  selector: 'glass-storage-smart-form',
  templateUrl: './storage-smart-form.component.html',
  styleUrls: ['./storage-smart-form.component.scss']
})
export class StorageSmartFormComponent {
  pageStatus: PageStatus = PageStatus.none;
  data: Array<SmartCtlAtaSmartAttribute> = [];
  columns: DatatableColumn[];

  private firstLoadComplete = false;
  private devicePath?: string;

  constructor(
    private devicesService: DevicesService,
    private localNodeService: LocalNodeService,
    private route: ActivatedRoute
  ) {
    this.columns = [
      {
        name: TEXT('ID'),
        prop: 'id',
        cols: 1
      },
      {
        name: TEXT('Name'),
        prop: 'name',
        css: 'text-truncate'
      },
      {
        name: TEXT('Flags'),
        prop: 'flags.string',
        cols: 1
      },
      {
        name: TEXT('Value'),
        prop: 'value',
        cols: 1
      },
      {
        name: TEXT('Worst'),
        prop: 'worst',
        cols: 1
      },
      {
        name: TEXT('Threshold'),
        prop: 'thresh',
        cols: 1
      },
      {
        name: TEXT('Raw value'),
        prop: 'raw.value',
        css: 'text-truncate'
      }
    ];

    this.route.params.subscribe((p: { path?: string }) => {
      this.devicePath = decodeURIComponent(p.path!);
      this.loadData();
    });
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
          const deviceHost: DeviceHost = _.get(res.devices, res.inventory.hostname);
          const device: Device | undefined = _.find(deviceHost.devices, ['path', this.devicePath]);
          if (device?.smart_metrics?.ata_smart_attributes) {
            this.data = device.smart_metrics.ata_smart_attributes.table;
          }
          this.pageStatus = PageStatus.ready;
        },
        () => (this.pageStatus = PageStatus.loadingError)
      );
  }
}
