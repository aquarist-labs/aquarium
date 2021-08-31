import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

import { DeclarativeFormModalComponent } from '~/app/core/modals/declarative-form/declarative-form-modal.component';
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
  loading = false;
  firstLoadComplete = false;
  data: Host[] = [];
  columns: DatatableColumn[];

  constructor(
    private dialogService: DialogService,
    private nodesService: NodesService,
    private orchService: OrchService
  ) {
    this.columns = [
      {
        name: TEXT('Hostname'),
        prop: 'hostname',
        sortable: true
      },
      {
        name: TEXT('Address'),
        prop: 'address',
        sortable: true
      }
    ];
  }

  loadData(): void {
    this.loading = true;
    this.orchService.hosts().subscribe((data) => {
      this.data = data;
      this.loading = this.firstLoadComplete = true;
    });
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
