import { Component, OnInit } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

import { DeclarativeFormModalComponent } from '~/app/core/modals/declarative-form/declarative-form-modal.component';
import { DatatableActionItem } from '~/app/shared/models/datatable-action-item.type';
import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { DatatableData } from '~/app/shared/models/datatable-data.type';
import { BytesToSizePipe } from '~/app/shared/pipes/bytes-to-size.pipe';
import { RedundancyLevelPipe } from '~/app/shared/pipes/redundancy-level.pipe';
import { CephFSAuthorization, CephfsService } from '~/app/shared/services/api/cephfs.service';
import { ServiceDesc, ServicesService } from '~/app/shared/services/api/services.service';
import { DialogService } from '~/app/shared/services/dialog.service';

@Component({
  selector: 'glass-services-page',
  templateUrl: './services-page.component.html',
  styleUrls: ['./services-page.component.scss']
})
export class ServicesPageComponent implements OnInit {
  loading = false;
  firstLoadComplete = false;
  data: ServiceDesc[] = [];
  columns: DatatableColumn[];

  constructor(
    private service: ServicesService,
    private bytesToSizePipe: BytesToSizePipe,
    private redundancyLevelPipe: RedundancyLevelPipe,
    private dialog: DialogService,
    private cephfsService: CephfsService,
    private dialogService: DialogService
  ) {
    this.columns = [
      {
        name: TEXT('Name'),
        prop: 'name',
        sortable: true
      },
      {
        name: TEXT('Type'),
        prop: 'type',
        sortable: true
      },
      {
        name: TEXT('Allocated Size'),
        prop: 'reservation',
        pipe: this.bytesToSizePipe,
        sortable: true
      },
      {
        name: TEXT('Raw Size'),
        prop: 'raw_size',
        pipe: this.bytesToSizePipe,
        sortable: true
      },
      {
        name: TEXT('Flavor'),
        prop: 'replicas',
        pipe: this.redundancyLevelPipe,
        sortable: true
      },
      {
        name: '',
        prop: '',
        cellTemplateName: 'actionMenu',
        cellTemplateConfig: this.onActionMenu.bind(this)
      }
    ];
    this.loadData();
  }

  ngOnInit(): void {}

  onAddService(type: string): void {
    switch (type) {
      case 'cephfs':
        this.dialog.openCephfs((res) => {
          if (res) {
            this.loadData();
          }
        });
        break;
      case 'nfs':
        this.dialog.openNfs((res) => {
          if (res) {
            this.loadData();
          }
        });
        break;
    }
  }

  loadData(): void {
    this.loading = true;
    this.service.list().subscribe((data) => {
      this.data = data;
      this.loading = this.firstLoadComplete = true;
    });
  }

  onActionMenu(serviceDesc: ServiceDesc): DatatableActionItem[] {
    const result: DatatableActionItem[] = [];
    switch (serviceDesc.type) {
      case 'cephfs':
        result.push({
          title: TEXT('Show credentials'),
          callback: (data: DatatableData) => {
            this.cephfsService.authorization(data.name).subscribe((auth: CephFSAuthorization) => {
              this.dialogService.open(DeclarativeFormModalComponent, undefined, {
                width: '40%',
                data: {
                  title: 'Credentials',
                  fields: [
                    {
                      type: 'text',
                      name: 'entity',
                      label: TEXT('Entity'),
                      value: auth.entity,
                      readonly: true
                    },
                    {
                      type: 'password',
                      name: 'key',
                      label: TEXT('Key'),
                      value: auth.key,
                      readonly: true
                    }
                  ],
                  okButtonVisible: false,
                  cancelButtonText: TEXT('Close')
                }
              });
            });
          }
        });
        break;
    }
    return result;
  }
}
