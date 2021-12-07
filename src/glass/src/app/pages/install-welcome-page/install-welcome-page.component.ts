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

import { bytesToSize } from '~/app/functions.helper';
import { Icon } from '~/app/shared/enum/icon.enum';
import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { DeployRequirementsReply, DeployService } from '~/app/shared/services/api/deploy.service';
import { NotificationService } from '~/app/shared/services/notification.service';

type TableEntry = {
  qualified: boolean;
  name: string;
  actual: string;
  min: string;
  error: string;
};

@Component({
  selector: 'glass-install-welcome-page',
  templateUrl: './install-welcome-page.component.html',
  styleUrls: ['./install-welcome-page.component.scss']
})
export class InstallWelcomePageComponent implements OnInit {
  @ViewChild('qualifiedColTpl', { static: true })
  public qualifiedColTpl!: TemplateRef<any>;

  @ViewChild('nodeConfigColTpl', { static: true })
  public nodeConfigColTpl!: TemplateRef<any>;

  public icons = Icon;
  public status: TableEntry[] = [];
  public checked = false;
  public qualified = false;
  public impossible = true;
  public statusColumns: DatatableColumn[] = [];

  constructor(
    private deployService: DeployService,
    private notificationService: NotificationService
  ) {}

  ngOnInit(): void {
    this.statusColumns.unshift(
      {
        name: TEXT('Qualified'),
        prop: 'qualified',
        cellTemplate: this.qualifiedColTpl,
        sortable: false
      },
      {
        name: TEXT('Name'),
        prop: 'name'
      },
      {
        name: TEXT('Node Configuration'),
        prop: 'actual',
        cellTemplate: this.nodeConfigColTpl
      },
      {
        name: TEXT('Minimum requirement'),
        prop: 'min'
      },
      {
        name: TEXT('Description'),
        prop: 'error'
      }
    );
  }

  checkRequirements(): void {
    this.deployService.requirements().subscribe(
      (res: DeployRequirementsReply) => {
        this.checked = true;
        const requirements = res.requirements;
        if (!requirements.qualified) {
          this.qualified = requirements.qualified;
          this.impossible = requirements.impossible;

          this.status = [
            {
              qualified: requirements.cpu.qualified,
              name: TEXT('CPU'),
              actual: String(requirements.cpu.actual_threads),
              min: String(requirements.cpu.min_threads),
              error: requirements.cpu.error
            },
            {
              qualified: requirements.mem.qualified,
              name: TEXT('Memory'),
              actual: bytesToSize(requirements.mem.actual_mem),
              min: bytesToSize(requirements.mem.min_mem),
              error: requirements.mem.error
            },
            {
              qualified: requirements.disks.available.qualified,
              name: TEXT('Available Disks'),
              actual: requirements.disks.available.actual.toString(),
              min: requirements.disks.available.min.toString(),
              error: requirements.disks.available.error
            },
            {
              qualified: requirements.disks.install.qualified,
              name: TEXT('Largest Disk'),
              actual: bytesToSize(requirements.disks.install.actual),
              min: bytesToSize(requirements.disks.install.min),
              error: requirements.disks.install.error
            }
          ];
        }
      },
      (err) => {
        err.preventDefault();
        this.notificationService.show(err.message, {
          type: 'error'
        });
      }
    );
  }
}
