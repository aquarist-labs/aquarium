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
import { Component, Input, OnInit, ViewChild } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import * as _ from 'lodash';
import { BlockUI, NgBlockUI } from 'ng-block-ui';

import { InstallWizardContext } from '~/app/pages/install-wizard/models/install-wizard-context.type';
import { DatatableComponent } from '~/app/shared/components/datatable/datatable.component';
import { Icon } from '~/app/shared/enum/icon.enum';
import {
  DatatableCellTemplateName,
  DatatableColumn
} from '~/app/shared/models/datatable-column.type';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { DeployDevicesReply, DeployService } from '~/app/shared/services/api/deploy.service';
import { Disk } from '~/app/shared/services/api/local.service';

type TableEntry = {
  path?: string;
  rotational: boolean;
  size: number;
};

@Component({
  selector: 'glass-storage-devices-step',
  templateUrl: './storage-devices-step.component.html',
  styleUrls: ['./storage-devices-step.component.scss']
})
export class StorageDevicesStepComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  @ViewChild('table', { static: true })
  public table!: DatatableComponent;

  @Input()
  context?: InstallWizardContext;

  public icons = Icon;
  public disks: Disk[] = [];
  public devicesColumns: DatatableColumn[] = [
    {
      name: TEXT('Path'),
      prop: 'path'
    },
    {
      name: TEXT('Type'),
      prop: 'rotational',
      cellTemplateName: DatatableCellTemplateName.badge,
      cellTemplateConfig: {
        map: {
          true: { value: TEXT('HDD'), class: 'glass-color-theme-gray-600' },
          false: { value: TEXT('NVMe/SSD'), class: 'glass-color-theme-yellow-500' }
        }
      }
    },
    {
      name: TEXT('Product'),
      prop: 'product'
    },
    {
      name: TEXT('Vendor'),
      prop: 'vendor'
    },
    {
      name: TEXT('Size'),
      prop: 'size',
      pipe: new BytesToSizePipe()
    }
  ];
  public selected: TableEntry[] = [];

  constructor(private deployService: DeployService) {}

  get completed(): boolean {
    return this.selected.length > 0;
  }

  ngOnInit(): void {
    this.deployService.devices().subscribe({
      next: (ddr: DeployDevicesReply) => {
        const disks = _.cloneDeep(
          _.filter(ddr.devices, (device) => device.rejected_reasons.length === 0)
        );

        // Update the selection.
        const selected: TableEntry[] = [];
        const storage = _.get(this.context!.config, 'storage', []);
        _.forEach(storage, (path) => {
          const entry: TableEntry | undefined = _.find(disks, ['path', path]);
          if (!_.isUndefined(entry)) {
            selected.push(entry);
          }
        });

        this.disks = disks;
        this.selected.splice(0, this.selected.length, ...selected);
      }
    });
  }

  updateContext(): void {
    if (this.context && this.completed) {
      _.merge(this.context.config, {
        storage: _.map(this.selected, 'path')
      });
    }
  }
}
