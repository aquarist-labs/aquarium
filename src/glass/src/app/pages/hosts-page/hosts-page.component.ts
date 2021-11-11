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
import { finalize } from 'rxjs/operators';

import { DeclarativeFormModalComponent } from '~/app/core/modals/declarative-form/declarative-form-modal.component';
import { PageStatus } from '~/app/shared/components/content-page/content-page.component';
import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { NodesService, TokenReply } from '~/app/shared/services/api/nodes.service';
import { Host, OrchService } from '~/app/shared/services/api/orch.service';
import { DialogService } from '~/app/shared/services/dialog.service';

@Component({
  selector: 'glass-hosts-page',
  templateUrl: './hosts-page.component.html',
  styleUrls: ['./hosts-page.component.scss']
})
export class HostsPageComponent {
  pageStatus: PageStatus = PageStatus.none;
  data: Host[] = [];
  columns: DatatableColumn[];

  private firstLoadComplete = false;

  constructor(
    private dialogService: DialogService,
    private nodesService: NodesService,
    private orchService: OrchService
  ) {
    this.columns = [
      {
        name: TEXT('Hostname'),
        prop: 'hostname'
      },
      {
        name: TEXT('Address'),
        prop: 'address'
      }
    ];
  }

  loadData(): void {
    if (!this.firstLoadComplete) {
      this.pageStatus = PageStatus.loading;
    }
    this.orchService
      .hosts()
      .pipe(
        finalize(() => {
          this.firstLoadComplete = true;
        })
      )
      .subscribe(
        (data) => {
          this.data = data;
          this.pageStatus = PageStatus.ready;
        },
        () => (this.pageStatus = PageStatus.loadingError)
      );
  }

  onShowToken(): void {
    this.nodesService.token().subscribe((res: TokenReply) => {
      this.dialogService.open(DeclarativeFormModalComponent, undefined, {
        title: TEXT('Authentication Token'),
        subtitle: TEXT('Use this token to authenticate a new node when adding it to the cluster.'),
        formConfig: {
          fields: [
            {
              type: 'text',
              name: 'token',
              value: res.token,
              readonly: true,
              hasCopyToClipboardButton: true,
              class: 'glass-text-monospaced'
            }
          ]
        },
        submitButtonVisible: false,
        cancelButtonText: TEXT('Close')
      });
    });
  }
}
