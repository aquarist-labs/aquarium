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
import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { BlockUI, NgBlockUI } from 'ng-block-ui';

import { translate } from '~/app/i18n.helper';
import { Icon } from '~/app/shared/enum/icon.enum';
import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import {
  Disk,
  DiskSolution,
  DiskTypeEnum,
  NodesService,
  RejectedDisk
} from '~/app/shared/services/api/nodes.service';

type TableEntry = {
  path?: string;
  type: string;
  size: number;
  useAs: string;
  isSystemDisk: boolean;
  isStorageDisk: boolean;
  isAvailable: boolean;
  rejectedReasons: string[];
};

@Component({
  selector: 'glass-local-devices-step',
  templateUrl: './local-devices-step.component.html',
  styleUrls: ['./local-devices-step.component.scss']
})
export class LocalDevicesStepComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  @ViewChild('availableTpl', { static: true })
  public availableTpl!: TemplateRef<any>;

  public icons = Icon;
  public disks: TableEntry[] = [];
  public devicesColumns: DatatableColumn[] = [
    {
      name: TEXT('Path'),
      prop: 'path'
    },
    {
      name: TEXT('Type'),
      prop: 'type'
    },
    {
      name: TEXT('Size'),
      prop: 'size',
      pipe: new BytesToSizePipe()
    },
    {
      name: TEXT('Function'),
      prop: 'useAs'
    }
  ];

  constructor(private nodesService: NodesService) {}

  ngOnInit(): void {
    this.devicesColumns.unshift({
      name: TEXT('Available'),
      prop: 'isAvailable',
      cellTemplate: this.availableTpl
    });

    this.nodesService.deploymentDiskSolution().subscribe({
      next: (solution: DiskSolution) => {
        const entries: TableEntry[] = [];
        if (solution.systemdisk) {
          const entry = this.consumeDisk(solution.systemdisk);
          entry.isAvailable = true;
          entry.isSystemDisk = true;
          entry.useAs = translate(TEXT('System'));
          entries.push(entry);
        }
        solution.storage.forEach((disk: Disk) => {
          const entry = this.consumeDisk(disk);
          entry.isStorageDisk = true;
          entry.isAvailable = true;
          entry.useAs = translate(TEXT('Storage'));
          entries.push(entry);
        });
        solution.rejected.forEach((rejected: RejectedDisk) => {
          const entry = this.consumeDisk(rejected.disk);
          entry.isAvailable = false;
          entry.rejectedReasons = rejected.reasons;
          entries.push(entry);
        });
        this.disks = entries;
      }
    });
  }

  private consumeDisk(disk: Disk): TableEntry {
    let typeStr = translate(TEXT('Unknown'));
    if (disk.type === DiskTypeEnum.hdd) {
      typeStr = translate(TEXT('HDD'));
    } else if (disk.type === DiskTypeEnum.ssd) {
      typeStr = translate(TEXT('SSD'));
    }
    return {
      path: disk.path,
      size: disk.size,
      type: typeStr,
      useAs: translate(TEXT('N/A')),
      isAvailable: false,
      isSystemDisk: false,
      isStorageDisk: false,
      rejectedReasons: []
    };
  }
}
