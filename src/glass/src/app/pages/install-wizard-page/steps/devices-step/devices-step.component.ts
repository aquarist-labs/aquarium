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
import { Device, OrchService } from '~/app/shared/services/api/orch.service';
import { NotificationService } from '~/app/shared/services/notification.service';
import { PollService } from '~/app/shared/services/poll.service';

@Component({
  selector: 'glass-devices-step',
  templateUrl: './devices-step.component.html',
  styleUrls: ['./devices-step.component.scss']
})
export class DevicesStepComponent implements OnInit {
  @BlockUI()
  blockUI!: NgBlockUI;

  devices: Device[] = [];
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
      prop: 'size',
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

  constructor(
    private notificationService: NotificationService,
    private orchService: OrchService,
    private pollService: PollService
  ) {}

  ngOnInit(): void {
    this.getDevices();
  }

  getDevices(): void {
    this.blockUI.start(TEXT('Please wait, fetching device information ...'));
    this.orchService
      .devices()
      .pipe(
        this.pollService.poll(
          (hostDevices): boolean => !Object.values(hostDevices).some((v) => v.devices.length),
          10,
          TEXT('Failed to fetch device information')
        )
      )
      .subscribe(
        (hostDevices) => {
          Object.values(hostDevices).forEach((v) => {
            this.devices = this.devices.concat(v.devices);
          });
          this.blockUI.stop();
        },
        (err) => {
          this.blockUI.stop();
          this.notificationService.show(err.toString(), {
            type: 'error'
          });
        }
      );
  }
}
