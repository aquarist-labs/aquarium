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
import { Component, OnInit } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { BlockUI, NgBlockUI } from 'ng-block-ui';

import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { Volume } from '~/app/shared/services/api/local.service';
import { LocalInventoryService } from '~/app/shared/services/api/local-inventory.service';

@Component({
  selector: 'glass-local-devices-step',
  templateUrl: './local-devices-step.component.html',
  styleUrls: ['./local-devices-step.component.scss']
})
export class LocalDevicesStepComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  devices: Volume[] = [];
  devicesColumns: DatatableColumn[] = [
    {
      name: '',
      prop: '_',
      cellTemplateName: 'icon',
      cellTemplateConfig: { name: 'mdi:server' }
    },
    {
      name: TEXT('Path'),
      prop: 'path',
      sortable: true
    },
    {
      name: TEXT('Type'),
      prop: 'human_readable_type',
      sortable: true
    },
    {
      name: TEXT('Size'),
      prop: 'sys_api.size',
      sortable: true,
      pipe: new BytesToSizePipe()
    },
    {
      name: TEXT('Available'),
      prop: 'available',
      sortable: true,
      cellTemplateName: 'yesNoIcon'
    }
  ];

  constructor(private localInventoryService: LocalInventoryService) {}

  ngOnInit(): void {
    this.localInventoryService.getDevices().subscribe({
      next: (devices: Volume[]) => {
        this.devices = devices;
      }
    });
  }
}
