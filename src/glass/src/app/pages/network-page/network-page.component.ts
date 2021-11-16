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
import { BlockUI, NgBlockUI } from 'ng-block-ui';
import { finalize } from 'rxjs/operators';

import { PageStatus } from '~/app/shared/components/content-page/content-page.component';
import { DatatableActionItem } from '~/app/shared/models/datatable-action-item.type';
import {
  DatatableCellTemplateName,
  DatatableColumn
} from '~/app/shared/models/datatable-column.type';
import { Interface, NetworkService } from '~/app/shared/services/api/network.service';

@Component({
  selector: 'glass-network-page',
  templateUrl: './network-page.component.html',
  styleUrls: ['./network-page.component.scss']
})
export class NetworkPageComponent {
  @BlockUI()
  blockUI!: NgBlockUI;

  pageStatus: PageStatus = PageStatus.none;
  data: Interface[] = [];
  columns: DatatableColumn[];

  private firstLoadComplete = false;

  constructor(private networkService: NetworkService, private router: Router) {
    this.columns = [
      {
        name: TEXT('Name'),
        prop: 'name'
      },
      {
        name: TEXT('Address'),
        prop: 'config.addr'
      },
      {
        name: TEXT('Type'),
        prop: 'config.bootproto',
        cellTemplateName: DatatableCellTemplateName.map,
        cellTemplateConfig: {
          dhcp: TEXT('DHCP'),
          static: TEXT('Static')
        }
      },
      {
        name: TEXT('Enabled'),
        prop: 'config.enabled',
        cellTemplateName: DatatableCellTemplateName.checkIcon
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
    this.networkService
      .list()
      .pipe(
        finalize(() => {
          this.firstLoadComplete = true;
        })
      )
      .subscribe(
        (data) => {
          this.pageStatus = PageStatus.ready;
          this.data = data;
        },
        () => (this.pageStatus = PageStatus.loadingError)
      );
  }

  getActionMenu(selected: Interface): DatatableActionItem[] {
    return [
      {
        title: TEXT('Edit'),
        callback: () => this.router.navigate([`dashboard/network/edit/${selected.name}`])
      }
    ];
  }
}
