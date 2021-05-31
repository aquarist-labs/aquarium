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
import _ from 'lodash';

import { ServiceDesc, ServicesService } from '~/app/shared/services/api/services.service';
import { DialogService } from '~/app/shared/services/dialog.service';

@Component({
  selector: 'glass-services-step',
  templateUrl: './services-step.component.html',
  styleUrls: ['./services-step.component.scss']
})
export class ServicesStepComponent {
  public cephfsList: ServiceDesc[] = [];
  public nfsList: ServiceDesc[] = [];

  constructor(private dialogService: DialogService, private services: ServicesService) {}

  public openFileServiceDialog(type: string): void {
    this.dialogService.openFileService((result) => {
      if (result) {
        this.updateServicesLists([type]);
      }
    }, type);
  }

  private updateServicesLists(serviceTypes: string[] = ['cephfs', 'nfs']): void {
    this.services.list().subscribe((result: ServiceDesc[]) => {
      serviceTypes.forEach((serviceType) => {
        switch (serviceType) {
          case 'cephfs': {
            this.cephfsList = _.filter(result, { type: 'cephfs' });
            break;
          }
          case 'nfs': {
            this.nfsList = _.filter(result, { type: 'nfs' });
            break;
          }
        }
      });
    });
  }
}
